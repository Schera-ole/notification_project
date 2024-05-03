import datetime

import requests
user_id = ['1sad', '123asd']
data = {
    'user_ids': user_id,
    'template_name': 'mail',
    'send_immediately': True,
    'send_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'variables': {'asd': 'text'}
}
requests.post('http://localhost:9090/send_notification/', json=data)





# data = {
#     'version': 1,
#     'name': 'mail',
#     'text': '''
#     Hiya {{ username }}!
#
#     You did the right choice by joining our cinema club!
#     We gonna send you some updates and news every second friday. So stay tuned!
#
#     See you!
#     Cinema Club''',
# }
# print(requests.post('http://localhost:9090/api/add_template/', json=data))
#
#
#
#
#
# print(requests.get('http://localhost:9090/api/get_templates/').text)