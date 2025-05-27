# from modules.llm_utils.translate_instruction import translate_step_title, enrich_step_title
#
# res = enrich_step_title(
#     "Click Local'\n'Extra Wide Big Bum Bike Saddle Seat Bicycle Gel Pad Soft Comfort For Bicycle UK",
#     '/Users/anthonyf/projects/grainedAI/WebAgentPipeline/src/sample_2_major_error/frames_marked/zGZa7D8dcPz19rH9KERpW_marked.jpeg')
# print(res)

from modules.llm_utils.check_if_goto_instruction import check_if_goto_instruction

todo = 'In the website "https://shop.app/", visit the store named "Fashion Nova" and add the first best selling product to cart.'
todo= 'Set the trip preferences as tent, electric site, and water hookup amenities in the account.'
todo = "Help me find newborn diapers on Target priced between $50 and $100, I don't mind paying a little more for comfort."
todo = 'Quote the second article from the "Latest News" section on the CNBC website.'
todo = '- Task 1: "Find me the top-rated hotels on kayak.com for family. I want to check their reviews to find the best options for my next trip."'
res = check_if_goto_instruction(todo)
print(res)