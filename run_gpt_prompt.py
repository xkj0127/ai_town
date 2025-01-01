import json
import math
import re
import sys

from LLM.moda_agent import ModaAgent

sys.path.append('../')

moda = ModaAgent()
can_go_place = ['医院', '咖啡店', '蜜雪冰城', '学校', '小芳家', '火锅店', '绿道', '小明家', '小王家', '肯德基',
                    '乡村基', '健身房', '电影院', '商场', '海边']


# 每日计划表
def run_gpt_prompt_generate_hourly_schedule(persona,now_time):
    def __func_clean_up(gpt_response):

        cr = gpt_response
        return cr

    def __func_validate(gpt_response):
        try:
            gpt_response = gpt_response.replace("```","").split("json")[1][1:]
            gpt_response = json.loads(gpt_response.strip('\n'))['output']
            total_time = sum(item[1] for item in gpt_response)
            # print(total_time)
            if total_time > 1920:
                return False
            __func_clean_up(gpt_response)
        except:
            return False
        return True

    generate_prompt = ModaAgent.generate_prompt(
        [persona,now_time],
        r"./LLM/prompt_template/生成日程安排时间表.txt")
    output = moda.ollama_safe_generate_response(generate_prompt, "", "你不需要调整，只需要给我输出一个最终的结果，我需要一个标准的数组格式", 5,
                                                        __func_validate, __func_clean_up)
    # print("run_gpt_prompt_generate_hourly_schedule",output)
    if "json" in output:
        output = output.replace("```", "").split("json")[1][1:]
        output = json.loads(output.strip('\n'))['output']
        return output

    else:
        # print(output)
        return output


# 每天苏醒时间
def run_gpt_prompt_wake_up_hour(persona,now_time,hourly_schedule):
    def __func_clean_up(gpt_response):
        cr = gpt_response
        return cr

    def __func_validate(gpt_response):
        try:
            if "output" in gpt_response:
                pattern = r'"output"\s*:\s*"([^"]+)"'
                match = re.search(pattern, gpt_response)
                output_value = match.group(1)
                __func_clean_up(output_value)
            else:
                return False
        except:
            return False
        return True
    generate_prompt = ModaAgent.generate_prompt(
        [persona,now_time,hourly_schedule],
        r"./LLM/prompt_template/起床时间.txt")
    output = moda.ollama_safe_generate_response(generate_prompt, "",
                                                        "只需要给我输出一个最终的结果不需要给我其他任何信息，我需要一个标准的日期格式，比如：07-01（表示早上七点零一分起床）",
                                                        3,
                                                        __func_validate, __func_clean_up)
    pattern = r'"output"\s*:\s*"([^"]+)"'
    match = re.search(pattern, output)
    output = match.group(1)
    return output

# 行动转表情
def run_gpt_prompt_pronunciatio(Action_dec):
    def __chat_func_clean_up(gpt_response):  
        cr = gpt_response.strip()
        if len(cr) > 3:
            cr = cr[:3]
        if len(cr) == 0:
            cr = '😴💤'
        return cr
    def __chat_func_validate(gpt_response):  
        try:
            gpt_response = json.loads(gpt_response)["output"]
            __chat_func_clean_up(gpt_response)
        except:
            return False
        return True
    example_output = "🛁🧖‍♀️"  ########
    special_instruction = "输出只包含表情符号"  ########
    generate_prompt = ModaAgent.generate_prompt(
        [Action_dec],
        r"./LLM/prompt_template/行为转为图标显示.txt")
    output = moda.ollama_safe_generate_response(generate_prompt, example_output, special_instruction, 5,__chat_func_validate,__chat_func_clean_up,'{"output":"🧘️"}')
    return json.loads(output)['output']


# 两个智能体间的对话
def double_agents_chat(maze,agent1_name,agent2_name,curr_context,init_summ_idea,target_summ_idea,now_time):
    def __chat_func_clean_up(gpt_response):
        try:
            output_value = json.loads(gpt_response)["output"]
        except:
            output_value = ""
        return output_value

    def __chat_func_validate(gpt_response):
        # print(type(gpt_response))
        try:
            output_value = json.loads(gpt_response)["output"]
            __chat_func_clean_up(output_value)
        except:
            return False
        return True

    generate_prompt = ModaAgent.generate_prompt(
        [maze,agent1_name, agent2_name, curr_context, init_summ_idea, target_summ_idea,now_time], r"./LLM/prompt_template/聊天.txt")

    example_output = '[["丹尼", "你好"], ["苏克", "你也是"] ... ]'
    special_instruction = '输出应该是一个列表类型，其中内部列表的形式为[“<名字>”，“<话语>”]。'

    output = moda.ollama_safe_generate_response(generate_prompt, example_output, special_instruction, 5,__chat_func_validate,__chat_func_clean_up,'''{"output":"[['小明', '明天去肯德基吗'], ['小芳', '好的，每天上午十一点在肯德基集合']]"}''')
    output = json.loads(output)["output"]
    return output


# 判断做这件事情需要去哪个地方
def go_map(agent_name, home , curr_place, can_go, curr_task):
    def __chat_func_clean_up(gpt_response):  
        return gpt_response

    def __chat_func_validate(gpt_response):  
        try:
            if "output" in gpt_response:
                pattern = r'"output"\s*:\s*"([^"]+)"'
                match = re.search(pattern, gpt_response)
                output_value = match.group(1)
                __chat_func_clean_up(output_value)
            else:
                return False
        except:
            return False
        return True

    example_output = '海边'
    special_instruction = ''

    generate_prompt = ModaAgent.generate_prompt(
        [agent_name,home , curr_place, can_go, curr_task],
        r"./LLM/prompt_template/行动需要去的地方.txt")

    output = moda.ollama_safe_generate_response(generate_prompt, example_output, special_instruction, 3,__chat_func_validate,__chat_func_clean_up)
    pattern = r'"output"\s*:\s*"([^"]+)"'
    match = re.search(pattern, output)
    output = match.group(1)
    return output


# 思考改变日程安排
def modify_schedule(old_schedule,now_time,memory,wake_time):
    def __func_clean_up(gpt_response):
        cr = gpt_response
        return cr

    def __func_validate(gpt_response):
        try:
            gpt_response = gpt_response.replace("```","").split("json")[1][1:]
            gpt_response = json.loads(gpt_response.strip('\n'))['output']
            __func_clean_up(gpt_response)
        except:
            return False
        return True

    generate_prompt = ModaAgent.generate_prompt(
        [old_schedule,now_time,memory,wake_time],
        r"D:\Python_workspace\rag_qwen\tools\LLM\prompt_template\细化每日安排时间表.txt")
    output = moda.ollama_safe_generate_response(generate_prompt, "", "你不需要调整，只需要给我输出一个最终的结果，我需要一个标准的数组格式", 10,
                                                        __func_validate, __func_clean_up)
    print("modify_schedule",output)
    if type(output) == str:
        if "json" in output:
            output = output.replace("```", "").split("json")[1][1:]
            output = json.loads(output.strip('\n'))['output']
            return output

        else:
            # print(output)
            return output
    else:
        return output


# 总结今天的一切写入记忆文件
def summarize(memory,now_time,name):
    def __chat_func_clean_up(gpt_response):  
        return gpt_response

    def __chat_func_validate(gpt_response):  
        try:
            __chat_func_clean_up(gpt_response)
        except:
            return False
        return True
    generate_prompt = ModaAgent.generate_prompt(
        [memory,now_time,name],
        r"./LLM/prompt_template/总结经历交谈为记忆.txt")
    example_output = ''
    special_instruction = ''
    output = moda.ollama_safe_generate_response(generate_prompt, example_output, special_instruction, 3,
                                                   __chat_func_validate, __chat_func_clean_up)

    # print('summarize',output)
    return output
