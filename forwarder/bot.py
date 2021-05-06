import requests
from vk import VkApi

with open('config') as f:
    exec(f.read())

def vk_mainloop():
    vk = VkApi(VK_TOKEN)
    for vk_message in vk.listen():
        print(vk_message)
        if vk_message['from_id'] < 0:
            continue
        vk.send_message(
                vk_message['text'],
                vk_message['from_id'],
                vk_message['id'])

if __name__ == "__main__":
    vk_mainloop()
    #vk_thread = threading.Thread(target=vk_mainloop)
    #tg_thread = threading.Thread(target=tg_mainloop)
