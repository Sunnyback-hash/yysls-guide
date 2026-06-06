# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('c:/Users/25441/WorkBuddy/2026-05-23-21-23-04/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

VIDEO_MAP = {
    "an1": [(0, "BV1H8cCz1ED1", "萌新入门攻略合集：从零开始的江湖之路"), (1, "BV1kfVo6KEdC", "最新最全游戏设置2.0版本")],
    "an2": [(0, "BV192iXBtEuH", "30分钟全方位萌新教学：新手必看")],
    "an3": [(0, "BV1X8o6BVEgA", "全流派心法搭配与强度解析")],
    "an4": [(0, "BV1X8o6BVEgA", "心法系统详解：从入门到搭配")],
    "an5": [(0, "BV1H8cCz1ED1", "新手避坑指南：少走冤枉路")],
    "ab1": [(0, "BV1X8o6BVEgA", "鸣金虹流派心法搭配与输出循环")],
    "ab2": [(0, "BV1ikcGedEXU", "裂石钧流派配装与爆发手法")],
    "ab3": [(0, "BV1X8o6BVEgA", "牵丝玉远程流派心法与连招")],
    "ab4": [(1, "BV1ikcGedEXU", "裂石威坦克T位配装与拉怪技巧")],
    "ab5": [(0, "BV1tywge6E3n", "全流派心法搭配一次捋清楚")],
    "am1": [(0, "BV1RVcDeFEXz", "全地图探索收集一条龙攻略")],
    "am2": [(0, "BV1qe6GYzEXE", "清河将军祠全收集一条龙带跑"), (1, "BV1RVcDeFEXz", "百草野七伐坡全收集攻略")],
    "am3": [(0, "BV1zW6kYZErp", "开封区域探索与奇遇全收集")],
    "am4": [(0, "BV18UPBebENX", "不见山与河西高等级区域探索")],
    "am5": [(0, "BV1vtVa6nExK", "青州蓬山探索100%全收集攻略")],
    "ad1": [(0, "BV1yjwFzbEZF", "风雨楼副本机制与通关技巧")],
    "ad2": [(0, "BV1yjwFzbEZF", "武库副本全流程及BOSS打法")],
    "ad3": [(0, "BV1yjwFzbEZF", "试剑副本心法经验速刷技巧")],
    "ad4": [(1, "BV1yjwFzbEZF", "流火袭星打铁花机制详解")],
    "ad5": [(0, "BV1yjwFzbEZF", "龙骧御六合10人团本保姆级攻略")],
    "ae1": [(0, "BV1bWonB2Egt", "进阶版调律终极奥义：垫子法2.0教学")],
    "ae2": [(0, "BV1bWonB2Egt", "左四件套搭配与套装选择")],
    "ae3": [(0, "BV1bWonB2Egt", "右四件防具减伤机制详解")],
    "ae4": [(0, "BV1bWonB2Egt", "弓箭弓决选择与远程装备搭配")],
    "ae5": [(1, "BV1bWonB2Egt", "传家宝装备承音石与转律系统")],
    "ap1": [(0, "BV1b6fHYwEwa", "PVP止戈论剑从零开始保姆级教学")],
    "ap2": [(0, "BV1AwNVemEfi", "鸢神PVP闪避抓硬直连招教学")],
    "ap3": [(1, "BV1b6fHYwEwa", "裂石威PVP防反心理博弈技巧")],
    "ap4": [(0, "BV1AwNVemEfi", "伞扇PVP控制爆发连招攻略")],
    "ap5": [(1, "BV1b6fHYwEwa", "3v3团战PVP阵容与配合教学")],
    "aev1": [(0, "BV1vtVa6nExK", "暑期版本杭州地图与新玩法前瞻")],
    "aev2": [(0, "BV1vtVa6nExK", "蓬山版本全解析：伙伴与文津馆")],
    "aev3": [(0, "BV1vtVa6nExK", "端午活动限定配饰获取攻略")],
    "aev4": [(0, "BV1vtVa6nExK", "六一活动100+表情与奖励指南")],
    "aev5": [(0, "BV1vtVa6nExK", "赋神联动绳镖外观获取方法")],
    "aev6": [(0, "BV1kfVo6KEdC", "千秋同襟抱版本活动全攻略")],
    "acl1": [(0, "BV1qe6GYzEXE", "清河全蹊跷位置地图90个收集")],
    "acl2": [(0, "BV1zW6kYZErp", "开封动态蹊跷与隐藏区域收集")],
    "acl3": [(0, "BV18UPBebENX", "不见山深泽绥乡全收集攻略")],
    "acl4": [(0, "BV18UPBebENX", "河西荒漠遗迹宝箱全收集")],
    "acl5": [(0, "BV1KqNee5E49", "万事知任务全攻略与隐藏彩蛋")],
    "ash1": [(0, "BV1KqNee5E49", "射覆玩法古物鉴定与真伪辨别")],
    "ash2": [(0, "BV1KqNee5E49", "开封古董商人商品刷新攻略")],
    "ash3": [(0, "BV1KqNee5E49", "文物图鉴青铜瓷器书画全收集")],
    "ash4": [(0, "BV1KqNee5E49", "古玩鉴定进阶技巧详解")],
    "ash5": [(0, "BV1KqNee5E49", "隐藏文物收集攻略：珍宝位置")],
    "ato1": [(0, "BV1bWonB2Egt", "伤害计算器DPS模拟使用指南")],
    "ato2": [(0, "BV1H8cCz1ED1", "每周刷新时间表与日常规划")],
    "ato3": [(0, "BV1H8cCz1ED1", "交易行低买高卖赚长鸣玉")],
    "ato4": [(0, "BV1bWonB2Egt", "心法经验速刷与加成堆叠")],
    "ato5": [(0, "BV1H8cCz1ED1", "成就系统隐藏成就获取指南")],
    "alr1": [(0, "BV1dkw4zxEej", "主线剧情深度解析：江湖恩怨")],
    "alr2": [(0, "BV1dkw4zxEej", "侠迹系统跨越百年的故事线")],
    "alr3": [(0, "BV1dkw4zxEej", "清河竹林旧居与将军祠传说")],
    "alr4": [(0, "BV1dkw4zxEej", "开封宋金战场与铁花工艺传说")],
    "alr5": [(0, "BV1dkw4zxEej", "江湖门派武学传承与故事")],
    "aec1": [(0, "BV1H8cCz1ED1", "长鸣玉稳定收入与消费规划")],
    "aec2": [(0, "BV1H8cCz1ED1", "百业帮会贡献与福利最大化")],
    "aec3": [(0, "BV1H8cCz1ED1", "材料采集与制造收益分析")],
    "aec4": [(0, "BV1H8cCz1ED1", "零氪经济指南：不花钱玩得舒服")],
    "aec5": [(0, "BV1H8cCz1ED1", "交易行高阶控价与稀有投资")],
    "aac1": [(0, "BV1RVcDeFEXz", "探索类成就地图收集汇总")],
    "aac2": [(0, "BV1yjwFzbEZF", "战斗类成就BOSS挑战攻略")],
    "aac3": [(0, "BV1H8cCz1ED1", "社交类成就组队协助指南")],
    "aac4": [(0, "BV1vtVa6nExK", "特殊成就限时活动版本纪念")],
    "aac5": [(0, "BV1H8cCz1ED1", "成就点奖励称号外观汇总")],
    "acb1": [(0, "BV1b6fHYwEwa", "格挡反击机制与防反时机练习")],
    "acb2": [(0, "BV1b6fHYwEwa", "耐力管理与完美闪避技巧")],
    "acb3": [(0, "BV1yjwFzbEZF", "BOSS战通用读技能与规避伤害")],
    "acb4": [(0, "BV1b6fHYwEwa", "连招系统真连伪连与技能取消")],
    "acb5": [(0, "BV1vtVa6nExK", "声骸系统外观幻化与收集")],
    "acp1": [(0, "BV1vtVa6nExK", "伙伴系统养成与好感度互动")],
    "acp2": [(0, "BV1vtVa6nExK", "伙伴对战猫猫大鹅1v1技巧")],
    "acp3": [(0, "BV1vtVa6nExK", "猫咪收集4只位置与解锁条件")],
    "acp4": [(0, "BV1vtVa6nExK", "大鹅收集3只位置与培养")],
    "acp5": [(0, "BV1vtVa6nExK", "宠物装备配饰与伙伴外观")],
    "ahs1": [(0, "BV1dkw4zxEej", "家园洞府建设与装饰指南")],
    "ahs2": [(0, "BV1dkw4zxEej", "留客巷匠造产业系统攻略")],
    "ahs3": [(0, "BV1dkw4zxEej", "家园装饰品稀有家具收集")],
    "ahs4": [(0, "BV1dkw4zxEej", "家园等级快速提升与材料收集")],
    "ahs5": [(0, "BV1dkw4zxEej", "家园社交好友互访与评比")],
    "aav1": [(0, "BV1bWonB2Egt", "105级毕业装备快速成型路线")],
    "aav2": [(0, "BV1bWonB2Egt", "心法9重突破材料获取攻略")],
    "aav3": [(0, "BV1bWonB2Egt", "战力提升从造诣到面板属性")],
    "aav4": [(0, "BV1H8cCz1ED1", "赛季制玩法重置与追赶机制")],
    "aav5": [(0, "BV1X8o6BVEgA", "多流派培养资源分配与心法通用")],
    "acmp1": [(0, "BV1yjwFzbEZF", "DPS排行榜伤害统计与输出优化")],
    "acmp2": [(0, "BV1yjwFzbEZF", "竞速副本速通技巧与路线优化")],
    "acmp3": [(0, "BV1yjwFzbEZF", "世界BOSS刷新时间表与击杀技巧")],
    "acmp4": [(0, "BV1yjwFzbEZF", "百业战帮会竞赛与团队协作")],
    "acmp5": [(0, "BV1b6fHYwEwa", "论剑登峰称号冲分心态管理")],
    "aph1": [(0, "BV1dkw4zxEej", "拍照模式滤镜构图与隐藏景点")],
    "aph2": [(0, "BV1dkw4zxEej", "绝美风景点推荐拍照圣地")],
    "aph3": [(0, "BV1dkw4zxEej", "人像拍照角色动作与光影运用")],
    "aph4": [(0, "BV1dkw4zxEej", "摄影大赛投稿技巧与获奖攻略")],
    "aph5": [(0, "BV1dkw4zxEej", "拍照模式天气调整与动作解锁")],
    "avr1": [(0, "BV1kfVo6KEdC", "2026年更新路线图全年规划")],
    "avr2": [(0, "BV1vtVa6nExK", "5月29日蓬山版本更新详情")],
    "avr3": [(0, "BV1kfVo6KEdC", "暑期版本杭州地图与新武学前瞻")],
    "avr4": [(0, "BV1kfVo6KEdC", "夹钟奏雅赛季回顾与大事记")],
    "avr5": [(0, "BV1kfVo6KEdC", "开发者访谈未来规划与反馈")],
    "avr6": [(0, "BV1vtVa6nExK", "千秋同襟抱版本完整解析")],
}

mod_count = 0
fail_count = 0

for aid, videos in VIDEO_MAP.items():
    pattern = '"id":"' + aid + '"'
    idx = content.find(pattern)
    if idx < 0:
        # Try ARTICLES_EN format
        pattern2 = '"' + aid + '":'
        idx = content.find(pattern2)
    if idx < 0:
        print("MISSING: " + aid)
        fail_count += 1
        continue

    sec_idx = content.find('"s":', idx)
    if sec_idx < 0:
        print("NO SECTIONS: " + aid)
        fail_count += 1
        continue

    first_brace = content.find('{', sec_idx)
    if first_brace < 0:
        print("NO BRACE: " + aid)
        fail_count += 1
        continue

    for sec_target_idx, bv_id, vt in videos:
        current_pos = first_brace
        for _ in range(sec_target_idx):
            close_brace = content.find('}', current_pos)
            next_brace = content.find('{', close_brace)
            if next_brace < 0:
                current_pos = -1
                break
            current_pos = next_brace

        if current_pos < 0:
            print("CANNOT FIND section " + str(sec_target_idx) + " for " + aid)
            fail_count += 1
            continue

        sec_close = content.find('}', current_pos)
        if sec_close < 0:
            print("NO CLOSING BRACE for " + aid + " section " + str(sec_target_idx))
            fail_count += 1
            continue

        section_content = content[current_pos:sec_close]
        if '"v":"' in section_content:
            print("ALREADY HAS VIDEO: " + aid)
            continue

        video_json = ',"v":"' + bv_id + '","vt":"' + vt + '"'
        content = content[:sec_close] + video_json + content[sec_close:]
        mod_count += 1
        sec_close += len(video_json)
        first_brace += len(video_json)

print("\n=== Result ===")
print("Modified: " + str(mod_count) + ", Failed: " + str(fail_count))

with open('c:/Users/25441/WorkBuddy/2026-05-23-21-23-04/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("File written successfully")
