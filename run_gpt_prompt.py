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
            print("total_time",total_time)
            if total_time > 2000:
                return False
            __func_clean_up(gpt_response)
        except:
            return False
        return True



    generate_prompt = ModaAgent.generate_prompt(
        [persona,now_time],
        r"./LLM/prompt_template/生成日程安排时间表.txt")
    output = moda.ollama_safe_generate_response(generate_prompt,
                                                "",
                                                "你没必要考虑我给的例子的时间，请帮我合理安排，严格遵守['时间']之和不能超过1920，你不需要调整，只需要给我输出一个最终的结果，我需要一个标准的数组格式,",
                                                10,
                                                __func_validate,
                                                __func_clean_up)
    # print(output)
    if "json" in output:
        output = output.replace("```", "").split("json")[1][1:]
        output = json.loads(output.strip('\n'))['output']
        return output

    else:
        # print(output)
        return output


# 每天苏醒时间
def run_gpt_prompt_wake_up_hour(persona,now_time,hourly_schedule):
    def __func_clean_up(gpt_response, prompt=""):
        cr = gpt_response
        return cr

    def __func_validate(gpt_response, prompt=""):
        try:
            if "output" in gpt_response:
                pattern = r'"output"\s*:\s*"([^"]+)"'
                match = re.search(pattern, gpt_response)
                output_value = match.group(1)
                __func_clean_up(output_value, prompt="")
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
                                                        5,
                                                        __func_validate, __func_clean_up)
    # print(output)
    pattern = r'"output"\s*:\s*"([^"]+)"'
    match = re.search(pattern, output)
    output = match.group(1)
    return output

# 行动转表情
def run_gpt_prompt_pronunciatio(Action_dec):
    def __chat_func_clean_up(gpt_response):  ############
        cr = gpt_response.strip()
        if len(cr) > 3:
            cr = cr[:3]
        return cr
    def __chat_func_validate(gpt_response):  ############
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
    output = moda.ollama_safe_generate_response(generate_prompt, example_output, special_instruction, 7,__chat_func_validate,__chat_func_clean_up,'{"output":"🧘️"}')
    return json.loads(output)['output']


# 两个智能体间的对话-test
def double_agents_chat(maze,agent1_name,agent2_name,curr_context,init_summ_idea,target_summ_idea):
    def __chat_func_clean_up(gpt_response):  ############
        return gpt_response

    def __chat_func_validate(gpt_response):  ############
        try:
            __chat_func_clean_up(gpt_response)
        except:
            return False
        return True

    generate_prompt = ModaAgent.generate_prompt(
        [maze,agent1_name, agent2_name, curr_context, init_summ_idea, target_summ_idea], r"./LLM\prompt_template/聊天.txt")

    example_output = '[["丹尼", "你好"], ["苏克", "你也是"] ... ]'
    special_instruction = '输出应该是一个列表类型，其中内部列表的形式为[“<名字>”，“<话语>”]。'

    x = moda.ollama_safe_generate_response(generate_prompt, example_output, special_instruction, 3,__chat_func_validate,__chat_func_clean_up)

    return json.loads(x)['output']


# 判断做这件事情需要去哪个地方
def go_map(agent_name, home , curr_place, can_go, curr_task):
    def __chat_func_clean_up(gpt_response):  ############
        return gpt_response

    def __chat_func_validate(gpt_response):  ############
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
    # print(output,"map")
    pattern = r'"output"\s*:\s*"([^"]+)"'
    match = re.search(pattern, output)
    output = match.group(1)
    return output

# 总结今天的一切写入记忆文件
def tess():
    pass

if __name__ == '__main__':
    class agent_v:
        def __init__(self, name, MAP):
            self.name = name
            self.MAP = MAP
            self.schedule = []
            self.Visual_Range = 1
            self.home = ""
            self.curr_place = ""
            self.position = (0, 0)
            self.schedule_time = []
            self.last_action = ""
            self.memory = ""
            self.wake = ""
            self.curr_action = ""
            self.curr_action_pronunciatio = ""
            self.ziliao = open(f"./agents/{self.name}/1.txt", encoding="utf-8").readlines()

        def getpositon(self):
            return self.position

        def goto_scene(self, scene_name):
            for row_index, row in enumerate(self.MAP):
                for col_index, cell in enumerate(row):
                    if cell == scene_name:
                        self.position = (row_index, col_index)
                        self.curr_place = scene_name
            return None  # 如果没有找到，返回 None

        def Is_nearby(self, position):
            x1 = self.position[0]
            x2 = position[0]
            y1 = self.position[1]
            y2 = position[1]
            manhattan_distance = abs(x1 - x2) + abs(y1 - y2)
            # 计算欧几里得距离
            euclidean_distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            # 判断是否相邻
            return manhattan_distance == 1 or euclidean_distance == 1 or euclidean_distance == math.sqrt(2)


    MAP = [['医院', '咖啡店', '#', '蜜雪冰城', '学校', '#', '#', '小芳家', '#', '#', '火锅店', '#', '#'],
           ['#', '#', '绿道', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
           ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
           ['#', '#', '#', '#', '#', '#', '小明家', '#', '小王家', '#', '#', '#', '#'],
           ['#', '#', '肯德基', '乡村基', '#', '#', '#', '#', '#', '#', '#', '健身房', '#'],
           ['电影院', '#', '#', '#', '#', '商场', '#', '#', '#', '#', '#', '#', '#'],
           ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
           ['#', '#', '#', '#', '#', '#', '#', '海边', '#', '#', '#', '#', '#']]
    agent1 = agent_v("小明", MAP)
    can_go_place = ['医院', '咖啡店', '蜜雪冰城', '学校', '小芳家', '火锅店', '绿道', '小明家', '小王家', '肯德基',
                    '乡村基', '健身房', '电影院', '商场', '海边']
    x = run_gpt_prompt_generate_hourly_schedule(agent1.ziliao[6],'2024-11-19')
    # print(x)
    # print(type(x))
