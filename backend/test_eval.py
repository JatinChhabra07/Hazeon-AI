from app.services.evaluation_service import run_evaluation
import traceback

try:
    print("Running evaluation...")
    res = run_evaluation(ocr_text='test', question_text='Discuss Panchayati Raj', question_marks=15, question_word_limit=250)
    print("Success!")
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
