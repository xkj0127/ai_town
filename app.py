import random
from datetime import datetime, timedelta
import gradio as gr
import numpy as np
from sklearn.cluster import DBSCAN
from run_gpt_prompt import *
import os

# print(os.getcwd())


# 小镇基本设施地图
MAP =    [['医院', '咖啡店', '#', '蜜雪冰城', '学校', '#', '#', '小芳家', '#', '#', '火锅店', '#', '#'],
          ['#', '#', '绿道', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
          ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
          ['#', '#', '#', '#', '#', '#', '小明家', '#', '小王家', '#', '#', '#', '#'],
          ['#', '#', '肯德基', '乡村基', '#', '#', '#', '#', '#', '#', '#', '健身房', '#'],
          ['电影院', '#', '#', '#', '#', '商场', '#', '#', '#', '#', '#', '#', '#'],
          ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
          ['#', '#', '#', '#', '#', '#', '#', '海边', '#', '#', '#', '#', '#']]

can_go_place = ['医院','咖啡店','蜜雪冰城', '学校','小芳家', '火锅店','绿道','小明家', '小王家','肯德基', '乡村基', '健身房','电影院', '商场','海边' ]

# TODO 暂时不考虑环境周围物品
objs = {
    "医院" : ["药","医生"],
    "咖啡店" : ["咖啡机","猫","咖啡","凳子"],
}

# 世界的规则
# TODO 暂时只考虑学校上学的时间，配合苏醒时间
world_rule = ""

# 角色
agents_name =  ["小明","小王","小芳"]

class agent_v:
    def __init__(self,name,MAP):
        self.name = name
        self.MAP = MAP
        self.schedule = []
        self.Visual_Range = 1
        self.home = ""
        self.curr_place  = ""
        self.position = (0,0)
        self.schedule_time = []
        self.last_action = ""
        self.memory = ""
        self.wake = ""
        self.curr_action = ""
        self.curr_action_pronunciatio  = ""
        self.ziliao = open(f"./agents/{self.name}/1.txt",encoding="utf-8").readlines()

    def getpositon(self):
        return self.position


    def goto_scene(self,scene_name):
        for row_index, row in enumerate(self.MAP):
            for col_index, cell in enumerate(row):
                if cell == scene_name:
                    self.position = (row_index,col_index)
                    self.curr_place =  scene_name
        return None  # 如果没有找到，返回 None

    def Is_nearby(self,position):
        x1=self.position[0]
        x2=position[0]
        y1=self.position[1]
        y2=position[1]
        manhattan_distance = abs(x1 - x2) + abs(y1 - y2)
        # 计算欧几里得距离
        euclidean_distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        # 判断是否相邻
        return manhattan_distance == 1 or euclidean_distance == 1 or euclidean_distance == math.sqrt(2)



# DBSCAN聚类方式感知聊天
def DBSCAN_chat(agents):
    result = []
    points_list =  []
    agent_list = []
    for agent in agents:
        points_list.append(agent.getpositon())
        agent_list.append(agent)
    points_array = np.array(points_list)
    dbscan = DBSCAN(eps=1.5, min_samples=1)
    labels = dbscan.fit_predict(points_array)

    for point, label,agent in zip(points_list, labels,agent_list):
        # print(f"Point {point} belongs to cluster {label}")
        index  = int(label)
        if index >= len(result):
            result.extend([[] for _ in range(index - len(result) + 1)])
        result[index] += [(point,agent)]
        # 筛选至少两个元素的聚类
    filtered_clusters = [cluster for cluster in result if len(cluster) >= 2]
    # 如果没有符合条件的聚类，返回 None
    if not filtered_clusters:
        return None
    if random.random() < 0.8:
        selected_cluster = random.choice(filtered_clusters)
        return [i[1] for i in selected_cluster]
    else:
        return None



# memory记忆 TODO 暂时考虑使用永久记忆，不设置遗忘曲线
'''
    记录：
        聊天的总结
        每天的工作计划
        这几天有什么重要的事情
'''

# 时间
START_TIME =  "2024-11-13-06-00"

# 计算时间的表示的函数
def get_now_time(oldtime,step_num,min_per_step):
    def format_time(dt):
        return dt.strftime("%Y-%m-%d-%H-%M")
    def calculate_new_time(oldtime, step_num):
        # 将字符串转换为 datetime 对象
        start_time = datetime.strptime(oldtime, "%Y-%m-%d-%H-%M")
        # 计算新的时间
        new_time = start_time + timedelta(minutes=min_per_step * step_num)
        # 将新的时间格式化为字符串
        return format_time(new_time)
    return calculate_new_time(oldtime, step_num)

# 获取时间对于的星期
def get_weekday(nowtime):
    date_format = '%Y-%m-%d-%H-%M'
    dt = datetime.strptime(nowtime, date_format)
    # 获取星期几，0表示星期一，6表示星期日
    weekday = dt.weekday()
    # 定义星期几的名称
    days_of_week = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期天"]
    return days_of_week[weekday]

# 时间转为2024年11月16日早上06点30分格式
def format_date_time(date_str):
    # 定义输入日期时间的格式
    input_format = '%Y-%m-%d-%H-%M'

    # 解析日期时间字符串
    dt = datetime.strptime(date_str, input_format)

    # 定义输出日期时间的格式
    output_format = '%Y年%m月%d日%H点%M分'

    # 格式化日期时间字符串
    formatted_date = dt.strftime(output_format)

    return formatted_date

# 比较两个时间谁更早
def compare_times(time_str1, time_str2, time_format="%H-%M"):
    # 解析时间字符串为 datetime 对象
    time1 = datetime.strptime(time_str1, time_format)
    time2 = datetime.strptime(time_str2, time_format)
    # 比较两个时间
    if time1 < time2:
        return True
    elif time1 > time2:
        return False
    else:
        return True


# 日程安排转为开始时间
#  TODO 时间有问题，睡觉时间,传入参数[1:]即可解决
def update_schedule(wake_up_time_str, schedule):
    # 将字符串格式的时间转换为datetime对象
    wake_up_time = datetime.strptime(wake_up_time_str, '%H-%M')
    # 初始化当前时间为醒来时间
    current_time = wake_up_time
    # 创建一个新的列表来存储更新后的日程安排
    updated_schedule = []
    for activity, duration in schedule:
        updated_schedule.append([activity, current_time.strftime('%H-%M')])
        current_time += timedelta(minutes=duration)

    return updated_schedule

# 确定当前时间agent开展的活动
def find_current_activity(current_time_str, schedule):
    print("now_time[-5:]",current_time_str)
    # 将当前时间字符串转换为datetime对象
    current_time = datetime.strptime(current_time_str, '%H-%M')
    # 遍历日程安排列表，找到当前时间对应的日程安排项
    for i, (activity, time_str) in enumerate(schedule):
        time_str = time_str.replace(':','-')
        # 将日程安排的时间字符串转换为datetime对象
        activity_time = datetime.strptime(time_str, '%H-%M')
        # 如果当前时间小于等于当前日程安排的时间，则返回当前日程安排项
        if current_time <= activity_time:
            return [activity, time_str]
    # 如果当前时间大于所有日程安排的时间，返回睡觉
    return ['睡觉',current_time_str]

# 文件处理部分
BASE_DIR = './agents/'
PARENT_DIRS = [os.path.join(BASE_DIR, folder) for folder in agents_name]
TARGET_FILENAME = "1.txt"  # 文件名相同

# 获取所有父文件夹中的目标文件路径
def get_target_files(parent_dirs, target_filename):
    target_files = {}
    for folder in parent_dirs:
        file_path = os.path.join(folder, target_filename)
        if os.path.exists(file_path):
            target_files[os.path.basename(folder)] = file_path
    return target_files

# 读取文件内容
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# 保存文件内容
def save_file(file_path, new_content):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(new_content)
    return f"文件 {os.path.basename(file_path)} 已成功保存！"

# 生成选项页函数
def generate_tabs(target_files):
    for folder_name, file_path in target_files.items():

        def save_callback(new_content, file_path=file_path):
            return save_file(file_path, new_content)

        with gr.Tab(folder_name):
            file_content = read_file(file_path)
            textbox = gr.Textbox(
                label=f"{folder_name}/{TARGET_FILENAME} 内容",
                value=file_content,
                lines=20,
                interactive=True
            )
            save_button = gr.Button("保存")
            save_status = gr.Label()

            save_button.click(save_callback, inputs=[textbox], outputs=save_status)

# 模拟主循环逻辑
def simulate_town_simulation(steps, min_per_step):
    output_gradio = []

    agent1 = agent_v("小明", MAP)
    agent2 = agent_v("小芳", MAP)
    agent3 = agent_v("小王", MAP)
    agent1.home = "小明家"
    agent2.home = "小芳家"
    agent3.home = "小王家"
    agents = [agent1, agent2, agent3]
    agent1.goto_scene("小明家")
    agent2.goto_scene("小芳家")
    agent3.goto_scene("小王家")
    step = 0
    now_time = START_TIME

    for i in range(steps):
        output_gradio.append(f'第 {i+1} 个 step'.center(150,'-'))
        len_tile = len(f'第 {i + 1} 个 step'.center(150, '-'))
        if step % int((1440 / min_per_step)) == 0:
            weekday_1 = get_weekday(START_TIME)
            format_time = format_date_time(START_TIME)
            output_gradio.append(f'当前时间：{format_time}({weekday_1})')
            for i in agents:
                if i.memory != "":
                    # print(i.name, i.memory)
                    i.memory = summarize(i.memory, f'{now_time[:10]}-{weekday_1}', i.name)
                i.goto_scene(i.home)
                i.schedule = run_gpt_prompt_generate_hourly_schedule(i.ziliao[6], f'{now_time[:10]}-{weekday_1}')
                i.wake = run_gpt_prompt_wake_up_hour(i.ziliao[6], now_time[:10]+weekday_1, i.schedule[1:])
                print("i.wake", i.wake)
                i.schedule_time = update_schedule(i.wake, i.schedule[1:])
                i.schedule_time = modify_schedule(i.schedule_time,f'{now_time[:10]}-{weekday_1}',i.memory,i.wake)
                print("i.schedule_time",i.schedule_time)
                i.curr_action = "睡觉"
                i.last_action = "睡觉"
                output_gradio.append(f'{i.name}当前活动:{i.curr_action}(😴💤)---所在地点({i.home})')
        else:
            weekday_2 = get_weekday(now_time)
            format_time = format_date_time(now_time)
            output_gradio.append(f'当前时间：{format_time}({weekday_2})')
            for i in agents:
                if compare_times(now_time[-5:], i.wake):
                    i.curr_action = "睡觉"
                    i.last_action = "睡觉"
                    i.curr_place = i.home
                    output_gradio.append(f'{i.name}当前活动:{i.curr_action}(😴💤)---所在地点({i.curr_place})')
                else:
                    if type(i.schedule_time) in [list]:
                        i.curr_action = find_current_activity(now_time[-5:], i.schedule_time)[0]
                    else:
                        pass
                    if i.last_action != i.curr_action:
                        i.curr_action_pronunciatio = run_gpt_prompt_pronunciatio(i.curr_action)[:2]
                        i.last_action = i.curr_action
                        i.curr_place = go_map(i.name, i.home, i.curr_place, can_go_place, i.curr_action)
                        i.goto_scene(i.curr_place)
                        output_gradio.append(
                            f'{i.name}当前活动:{i.curr_action}({i.curr_action_pronunciatio})---所在地点({i.curr_place})')
                    else:
                        output_gradio.append(
                            f'{i.name}当前活动:{i.curr_action}({i.curr_action_pronunciatio})---所在地点({i.curr_place})')
            # 感知周围其他角色决策行动
                # 主视角查看全地图，获取角色坐标
                    # 触发聊天
                        # 反思聊天变成记忆存储
                # 行动完成
            chat_part = DBSCAN_chat(agents)
            if chat_part == None:
                pass
            else:
                output_gradio.append(
                    f'{chat_part[0].name}和{chat_part[1].name}在{chat_part[1].curr_place}相遇,他们在进行聊天')
                chat_part[0].curr_action = "聊天"
                chat_part[1].curr_action = "聊天"

                if chat_part[0].curr_place == chat_part[1].curr_place:
                    output_gradio.append(
                        f'{chat_part[0].name}当前活动:{chat_part[0].curr_action}---所在地点({chat_part[0].curr_place}旁)')
                    output_gradio.append(
                        f'{chat_part[1].name}当前活动:{chat_part[1].curr_action}---所在地点({chat_part[0].curr_place}旁)')
                else:
                    output_gradio.append(
                        f'{chat_part[0].name}当前活动:{chat_part[0].curr_action}---所在地点({chat_part[0].curr_place}和{chat_part[1].curr_place}旁)')
                    output_gradio.append(
                        f'{chat_part[1].name}当前活动:{chat_part[1].curr_action}---所在地点({chat_part[0].curr_place}和{chat_part[1].curr_place}旁)')
                chat_result = double_agents_chat(
                    chat_part[0].curr_place,
                    chat_part[0].name,
                    chat_part[1].name,
                    f"{chat_part[0].name}正在{chat_part[0].curr_action},{chat_part[1].name}正在{chat_part[1].curr_action}",
                    chat_part[0].memory,
                    chat_part[1].memory,
                    f'{now_time[:10]}-{weekday_2}')
                output_gradio.append(f'聊天内容:{chat_result}')
                # print(343, type(chat_result))
                # print(344, type( chat_part[0].memory))
                # print(345, chat_result)
                chat_part[0].memory += json.dumps(chat_result, ensure_ascii=False)
                chat_part[1].memory += json.dumps(chat_result, ensure_ascii=False)




        step += 1
        now_time = get_now_time(now_time, 1,min_per_step)
        if step == steps:
            output_gradio.append("已到最大执行步数，结束".center(130, '-'))
        # 在每个循环结束时返回结果
        yield "\n".join(output_gradio)



# Gradio界面
def launch_gradio_interface():
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 小镇活动模拟")
                steps_input = gr.Number(value=60, label="模拟步数")
                min_per_step_input = gr.Number(value=30, label="每步模拟分钟数")
                simulation_output = gr.Textbox(label="模拟结果", interactive=False)

                simulate_button = gr.Button("开始模拟")
                simulate_button.click(simulate_town_simulation,
                                      inputs=[steps_input, min_per_step_input],
                                      outputs=[simulation_output])

            with gr.Column():
                gr.Markdown("### 编辑文件")
                target_files = get_target_files(PARENT_DIRS, TARGET_FILENAME)
                generate_tabs(target_files)

    demo.launch()

if __name__ == "__main__":
    launch_gradio_interface()
    # TODO 总结一天的，不要覆盖聊天记录而是+=