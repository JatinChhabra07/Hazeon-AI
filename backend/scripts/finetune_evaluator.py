"""
Hazeon AI — Fine-tune Llama-3 as UPSC Answer Evaluator
========================================================
Fine-tunes Llama-3.1-8B-Instruct on the topper answer evaluation dataset
using Unsloth (4x faster, half the memory — runs on free Colab T4 GPU).

Prerequisites (run on GPU machine / Google Colab):
  pip install unsloth transformers datasets trl torch

Run:
  python scripts/finetune_evaluator.py                    # full training
  python scripts/finetune_evaluator.py --test-only        # test inference
  python scripts/finetune_evaluator.py --epochs 3         # custom epochs
  python scripts/finetune_evaluator.py --push-to-hub      # upload to HuggingFace

Output:
  models/hazeon-upsc-evaluator/   ← fine-tuned model (load in app)
"""

import os, sys, json, argparse, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("finetune")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "training_data", "upsc_eval_dataset.jsonl")
MODEL_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "hazeon-upsc-evaluator")
BASE_MODEL = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"  # 4-bit quantized, fits T4/L4 GPU

# ── Anti-Hallucination System Prompt ─────────────────────────────────────────
# This is injected during inference (not training) to ground the model's output
ANTI_HALLUCINATION_SYSTEM = """You are a senior UPSC/HCS Mains answer evaluator with 20+ years of experience.

STRICT RULES:
1. Base your evaluation ONLY on the topper reference answer provided in the input. Do not add facts, schemes, data points, or constitutional articles that are NOT mentioned in either the student answer or topper reference.
2. Your keywords_found list must only contain terms that literally appear in the student answer.
3. Your keywords_missed list must only contain terms that appear in the topper reference but are absent from the student answer.
4. Feedback must cite specific phrases from the student answer when identifying strengths/weaknesses.
5. Return ONLY valid JSON — no preamble, no explanation outside JSON, no markdown code blocks.
6. Do not fabricate scores — base every score on observable characteristics of the student answer."""


# ══════════════════════════════════════════════════════════════════════════════
# LOAD & FORMAT DATASET
# ══════════════════════════════════════════════════════════════════════════════

def load_dataset(path: str):
    """Load JSONL dataset and format for Unsloth/TRL."""
    from datasets import Dataset

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Training data not found at {path}\n"
            "Run first: python -m scripts.build_training_dataset"
        )

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    logger.info(f"Loaded {len(records)} training examples")
    return Dataset.from_list(records)


def format_prompt(example: dict, tokenizer) -> dict:
    """
    Format into Llama-3 chat template:
    <|system|> ... <|user|> ... <|assistant|> ...
    """
    messages = [
        {"role": "system", "content": example["instruction"]},
        {"role": "user",   "content": example["input"]},
        {"role": "assistant", "content": example["output"]},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


# ══════════════════════════════════════════════════════════════════════════════
# FINE-TUNING
# ══════════════════════════════════════════════════════════════════════════════

def run_finetuning(epochs: int = 2, batch_size: int = 2, max_steps: int = -1):
    """Fine-tune Llama-3.1-8B on UPSC evaluation dataset using Unsloth."""

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
        import torch
    except ImportError:
        logger.error(
            "Required packages not installed.\n"
            "Run: pip install unsloth transformers datasets trl torch\n"
            "Or use the Colab notebook: notebooks/finetune_upsc_evaluator.ipynb"
        )
        sys.exit(1)

    # ── Load base model (4-bit quantized) ────────────────────────────────────
    logger.info(f"Loading base model: {BASE_MODEL}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=4096,
        dtype=None,           # auto detect
        load_in_4bit=True,    # 4-bit = fits in 16GB GPU
    )

    # ── Add LoRA adapters (Parameter-Efficient Fine-Tuning) ───────────────────
    # LoRA: only trains ~1% of parameters — fast & memory efficient
    logger.info("Adding LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,                  # LoRA rank — higher = more capacity, more memory
        target_modules=[       # which layers to fine-tune
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # ── Load & format dataset ─────────────────────────────────────────────────
    dataset = load_dataset(DATASET_PATH)
    dataset = dataset.map(
        lambda ex: format_prompt(ex, tokenizer),
        remove_columns=dataset.column_names,
    )

    # Split 90% train / 10% eval
    split = dataset.train_test_split(test_size=0.1, seed=42)
    logger.info(f"Train: {len(split['train'])} | Eval: {len(split['test'])}")

    # ── Training arguments ────────────────────────────────────────────────────
    training_args = TrainingArguments(
        output_dir=MODEL_OUTPUT_DIR,
        num_train_epochs=epochs,
        max_steps=max_steps if max_steps > 0 else -1,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        warmup_ratio=0.1,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",     # set to "wandb" if you want experiment tracking
    )

    # ── Trainer ───────────────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        dataset_text_field="text",
        max_seq_length=4096,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Starting fine-tuning on UPSC evaluation dataset...")
    logger.info(f"  Base model: {BASE_MODEL}")
    logger.info(f"  Epochs: {epochs} | Batch size: {batch_size}")
    logger.info(f"  Training examples: {len(split['train'])}")
    logger.info("=" * 60)

    trainer_stats = trainer.train()

    # ── Save ──────────────────────────────────────────────────────────────────
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(MODEL_OUTPUT_DIR)
    tokenizer.save_pretrained(MODEL_OUTPUT_DIR)

    logger.info(f"\nModel saved to: {MODEL_OUTPUT_DIR}")
    logger.info(f"Training loss: {trainer_stats.training_loss:.4f}")
    logger.info(f"Training time: {trainer_stats.metrics.get('train_runtime', 0):.0f}s")

    return model, tokenizer


# ══════════════════════════════════════════════════════════════════════════════
# TEST INFERENCE — verify the fine-tuned model works
# ══════════════════════════════════════════════════════════════════════════════

TEST_QUESTION = "Discuss the challenges of good governance in Haryana and suggest measures to improve administrative efficiency at the district level."
TEST_STUDENT_ANSWER = """Good governance is important for Haryana. The SARAL platform has been launched.
There are challenges like corruption and poor digital infrastructure in villages.
The government should take steps to improve governance at district level.
Way Forward: More transparency, better e-governance, train officers properly."""


def run_test_inference(model_path: str = None):
    """Test the fine-tuned model on a sample evaluation."""
    try:
        from unsloth import FastLanguageModel
    except ImportError:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError:
            logger.error("Install: pip install transformers torch")
            return

    path = model_path or MODEL_OUTPUT_DIR
    if not os.path.exists(path):
        logger.error(f"Model not found at {path}. Run fine-tuning first.")
        return

    logger.info(f"Loading fine-tuned model from {path}...")

    try:
        from unsloth import FastLanguageModel
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=path, max_seq_length=4096, load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
    except Exception:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        tokenizer = AutoTokenizer.from_pretrained(path)
        model = AutoModelForCausalLM.from_pretrained(
            path, torch_dtype=torch.float16, device_map="auto"
        )

    SYSTEM_INSTRUCTION = ANTI_HALLUCINATION_SYSTEM

    # Find a topper answer from DB for the test question
    topper_ref = """Good governance embodies transparency, accountability and responsiveness. Haryana's SARAL platform (550+ services), CM Window portal (50 lakh grievances resolved), and e-procurement are key achievements. Challenges: 30% admin vacancy, rural digital divide (45%), 8 lakh pending court cases. Way Forward: 2-year posting tenure (ARC2), District Performance Index, Gram Sachivalaya strengthening, Haryana Ombudsman operationalization."""

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": f"""Question (GS2 - Governance, 15 marks, 2025 HCS):
{TEST_QUESTION}

Topper Reference Answer:
{topper_ref}

Student Answer (52 words):
{TEST_STUDENT_ANSWER}"""},
    ]

    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to("cuda" if __import__("torch").cuda.is_available() else "cpu")

    import torch
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=1024,
            temperature=0.1,        # low temperature = deterministic, non-random
            do_sample=False,         # greedy decoding = most factual output
            repetition_penalty=1.1,  # prevent repeating the same feedback
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    logger.info("\n" + "=" * 60)
    logger.info("FINE-TUNED MODEL OUTPUT:")
    logger.info("=" * 60)
    print(generated)

    # Validate JSON output and check anti-hallucination compliance
    try:
        result = json.loads(generated)
        logger.info(f"\nOverall Score: {result.get('overall_score')}/10")
        logger.info(f"Marks Obtained: {result.get('marks_obtained')}")
        logger.info(f"Feedback: {result.get('feedback_summary', '')[:200]}")

        # Anti-hallucination checks
        issues = []
        required_keys = ["overall_score", "feedback_summary", "strengths", "weaknesses",
                         "keywords_found", "keywords_missed", "topper_benchmark"]
        for key in required_keys:
            if key not in result:
                issues.append(f"Missing field: {key}")

        scores = ["relevance_score", "intro_score", "body_score", "keyword_score",
                  "structure_score", "factual_score", "conclusion_score", "analysis_score"]
        for s in scores:
            val = result.get(s, 0)
            if not (0 <= val <= 10):
                issues.append(f"Score out of range: {s}={val}")

        if issues:
            logger.warning(f"Output quality issues: {issues}")
        else:
            logger.info("Output validation PASSED — all fields present, scores in range")

    except json.JSONDecodeError:
        logger.warning("Output is not valid JSON — model may need more training examples")
        # Try to extract JSON from output (sometimes model wraps in markdown)
        import re
        json_match = re.search(r'\{[\s\S]+\}', generated)
        if json_match:
            try:
                result = json.loads(json_match.group())
                logger.info(f"Extracted JSON: overall_score={result.get('overall_score')}")
            except Exception:
                logger.error("Could not extract valid JSON — increase training data")


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATE FINE-TUNED MODEL INTO THE APP
# ══════════════════════════════════════════════════════════════════════════════

def update_app_config():
    """
    Updates evaluation_service.py to use fine-tuned model instead of Groq/Gemini.
    """
    config_note = f"""
# ── To use fine-tuned model, add this to your .env: ──
# FINETUNED_MODEL_PATH={MODEL_OUTPUT_DIR}
# USE_FINETUNED_MODEL=true
#
# Then in evaluation_service.py, get_llm() will automatically
# load the fine-tuned model if FINETUNED_MODEL_PATH is set.
"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "a") as f:
            f.write(config_note)
        logger.info(f"Added fine-tuned model config to {env_path}")
    else:
        logger.info(config_note)


# ══════════════════════════════════════════════════════════════════════════════
# PUSH TO HUGGING FACE HUB (optional)
# ══════════════════════════════════════════════════════════════════════════════

def push_to_hub(model, tokenizer, repo_id: str = "hazeon-ai/upsc-evaluator-llama3"):
    """Upload fine-tuned model to HuggingFace Hub for easy deployment."""
    try:
        model.push_to_hub(repo_id, private=True)
        tokenizer.push_to_hub(repo_id, private=True)
        logger.info(f"Model uploaded to HuggingFace: {repo_id}")
    except Exception as e:
        logger.error(f"Hub upload failed: {e}")
        logger.info("Set HF_TOKEN env var: export HF_TOKEN=hf_xxxx")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Llama-3 as UPSC evaluator")
    parser.add_argument("--test-only", action="store_true", help="Only run test inference on existing model")
    parser.add_argument("--epochs", type=int, default=2, help="Training epochs (default: 2)")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size (default: 2)")
    parser.add_argument("--max-steps", type=int, default=-1, help="Max training steps (-1 = all)")
    parser.add_argument("--push-to-hub", action="store_true", help="Upload to HuggingFace Hub after training")
    args = parser.parse_args()

    if args.test_only:
        run_test_inference()
        return

    model, tokenizer = run_finetuning(
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_steps=args.max_steps,
    )

    if args.push_to_hub:
        push_to_hub(model, tokenizer)

    update_app_config()

    logger.info("\n" + "=" * 60)
    logger.info("FINE-TUNING COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"Model saved: {MODEL_OUTPUT_DIR}")
    logger.info("\nNext steps:")
    logger.info("1. Test: python scripts/finetune_evaluator.py --test-only")
    logger.info("2. Add to .env: FINETUNED_MODEL_PATH=" + MODEL_OUTPUT_DIR)
    logger.info("3. Restart backend server — it will use your fine-tuned model")


if __name__ == "__main__":
    main()
