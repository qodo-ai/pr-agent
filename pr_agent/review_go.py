import asyncio
from functools import partial

from review_agent.algo.ai_handlers.deepseek_ai_handler import DeepSeekHandler
from review_agent.algo.ai_handlers.openai_ai_handler import OpenAIHandler
from review_agent.algo.utils import load_yaml, github_action_output, convert_to_markdown_v2
from review_agent.config_loader import get_settings
from jinja2 import Environment, StrictUndefined

async def main():
    diff = """
     Additional modified files (insufficient token budget to process):
     redisson/src/main/java/org/redisson/pubsub/PublishSubscribeService.java
     
     if (!ee.getEntries().contains(entry)) {
        if (entry.getConnection().isClosed()) {
            ee.getEntries().remove(entry);
        } else if (!ee.getEntries().contains(entry)) {
    """
    variables = {
        "is_ai_metadata": False,
        "extra_instructions": "",
        "require_can_be_split_review": False,
        "duplicate_prompt_examples": False,
        "require_estimate_effort_to_review": True,
        "require_score": False,
        "require_tests": True,
        "require_security_review": True,
        "related_tickets": [],
        "question_str": "",
        "title": "Fixed - PubSub stops working after Redis restart in sentinel mode #6026 #6541",
        "branch": "seakider:fix_pubsub_conn",
        "description": "",
        "answer_str": "",
        "diff": diff,
        "num_pr_files": 1
    }

    global_settings = get_settings()
    environment = Environment(undefined=StrictUndefined)
    system_prompt = environment.from_string(global_settings.pr_review_prompt.system).render(variables)
    user_prompt = environment.from_string(global_settings.pr_review_prompt.user).render(variables)


    #print(user_prompt)
    #ai_handler = DeepSeekHandler()
    ai_handler = OpenAIHandler()
    response, finish_reason = await ai_handler.chat_completion(
        model='gpt-4o-2024-08-06',
        temperature=get_settings().config.temperature,
        system=system_prompt,
        user=user_prompt
    )
    print(response)

     #打印换行字符串行
    print('##########################################')
    first_key = 'review'
    last_key = 'security_concerns'
    data = load_yaml(response.strip(),
                     keys_fix_yaml=["ticket_compliance_check", "estimated_effort_to_review_[1-5]:",
                                    "security_concerns:", "key_issues_to_review:",
                                    "relevant_file:", "relevant_line:", "suggestion:"],
                     first_key=first_key, last_key=last_key)
    github_action_output(data, 'review')

    # move data['review'] 'key_issues_to_review' key to the end of the dictionary
    if 'key_issues_to_review' in data['review']:
        key_issues_to_review = data['review'].pop('key_issues_to_review')
        data['review']['key_issues_to_review'] = key_issues_to_review

    incremental_review_markdown_text = None


    markdown_text = convert_to_markdown_v2(data, True,
                                           incremental_review_markdown_text,
                                           None,
                                           None)

    print(markdown_text)

if __name__ == '__main__':
    asyncio.run(main())