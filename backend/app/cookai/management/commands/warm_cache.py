# cookai/management/commands/warm_cache.py
from django.core.management.base import BaseCommand
from cookai.models import AIPrompt

class Command(BaseCommand):
    help = "Preload default prompts"

    DEFAULTS = {
        "score":   "给下列美食照片打 0-100 分并解释：{urls}",
        "compare": "比较这两张菜品照 {urls} 谁更好，输出 JSON {\"winner\":1/2/0,\"reason\":\"...\"}",
        "detect":  "识别 {urls} 中出现的食材，以 JSON 数组返回",
    }

    def handle(self, *args, **kwargs):
        for k, tpl in self.DEFAULTS.items():
            AIPrompt.objects.get_or_create(kind=k, name=f"default_{k}", defaults={"template": tpl})
        self.stdout.write(self.style.SUCCESS("Prompts ensured"))
