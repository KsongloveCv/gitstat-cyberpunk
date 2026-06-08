"""Webhook notifications for Slack/DingTalk/Feishu."""
import json
import urllib.request as ur
import logging

log = logging.getLogger('gitstat.webhook')


def send_webhook(url: str, title: str, text: str, platform: str = "slack") -> bool:
    """Send markdown message to webhook URL. Supports slack/dingtalk/feishu."""
    try:
        if platform == "dingtalk":
            payload = {
                "msgtype": "markdown",
                "markdown": {"title": title, "text": f"## {title}\n\n{text}"}
            }
        elif platform == "feishu":
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {"title": {"tag": "plain_text", "content": title}},
                    "elements": [{"tag": "markdown", "content": text}]
                }
            }
        else:  # slack
            payload = {"text": f"*{title}*\n{text}"}

        req = ur.Request(url, data=json.dumps(payload).encode(),
                         headers={"Content-Type": "application/json"})
        with ur.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        log.warning("Webhook send failed: %s", e)
        return False


def send_daily_summary(webhook_url: str, platform: str = "slack"):
    """Generate and send daily summary via webhook."""
    import sys
    sys.path.insert(0, '.')
    from main import store, aggregate_overview
    repos = store.get_repositories()
    if not repos:
        return

    from datetime import datetime
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    o = aggregate_overview(repos, "", today, datetime.now())

    text = (
        f"📊 今日统计\n"
        f"• 提交: {o.get('totalCommits', 0)}\n"
        f"• 新增: +{o.get('totalAdditions', 0)} 行\n"
        f"• 删除: -{o.get('totalDeletions', 0)} 行\n"
        f"• 活跃作者: {o.get('activeAuthors', 0)} 人"
    )
    send_webhook(webhook_url, f"GitStat 日报 {datetime.now().strftime('%m/%d')}", text, platform)
