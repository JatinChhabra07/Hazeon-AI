from PIL import Image, ImageDraw, ImageFont
import textwrap

# Setup
width, height = 800, 1000
img = Image.new('RGB', (width, height), color=(255, 255, 255))
d = ImageDraw.Draw(img)

# Try to use a standard font, fallback to default
try:
    font_title = ImageFont.truetype("arialbd.ttf", 24)
    font_text = ImageFont.truetype("arial.ttf", 18)
except IOError:
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()

# Draw margins (simulating a standard UPSC answer sheet)
d.line([(80, 0), (80, height)], fill=(200, 200, 200), width=2)
for y in range(80, height, 40):
    d.line([(80, y), (width - 40, y)], fill=(230, 230, 230), width=1)

# Content
y_text = 60
d.text((100, y_text), "Q1: Discuss the impact of climate change on Indian agriculture.", font=font_title, fill=(0, 0, 0))
y_text += 50

answer_text = """
Climate change poses a severe threat to Indian agriculture, which is heavily 
dependent on the monsoons. The impacts are multidimensional:

1. Changing Monsoon Patterns: Erratically shifting rainfall patterns lead 
to severe droughts in some regions and floods in others, directly 
affecting the Kharif crop sowing schedule.

2. Temperature Rise: A sudden spike in temperatures during the wheat 
growing season (terminal heat stress) significantly reduces crop yields 
in North India. This threatens national food security.

3. Pest and Disease Outbreaks: Warmer climates expand the geographical 
range of pests like locusts and pathogens, causing newly emerging 
crop diseases that farmers are unprepared for.

4. Water Scarcity: Himalayan glaciers are retreating, which will eventually 
reduce the flow of perennial rivers like the Ganga, affecting irrigation 
in the fertile northern plains.

Conclusion:
To mitigate these impacts, India must adopt climate-resilient agriculture, 
invest heavily in micro-irrigation, develop heat-resistant seed varieties, 
and strengthen the early warning systems for farmers.
"""

lines = answer_text.strip().split('\n')
for line in lines:
    d.text((100, y_text), line, font=font_text, fill=(20, 20, 80))  # Blueish-black ink
    y_text += 30

# Save
img.save("e:/Demo-Work/sample_answer.jpg")
print("Sample answer generated successfully at e:/Demo-Work/sample_answer.jpg")
