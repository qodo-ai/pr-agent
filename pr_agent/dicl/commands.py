from pr_agent.dicl.sdk import DICL
from pr_agent.config_loader import get_settings
from pr_agent.tools.pr_reviewer import PRReviewer

class DICLIngest:
    def __init__(self, pr_url: str, ai_handler=None, args: list = None):
        self.pr_url = pr_url
        self.args = args or []
        
    async def run(self):
        max_prs = 10
        for arg in self.args:
            if arg.startswith("--max-prs="):
                max_prs = int(arg.split("=")[1])
        
        result = DICL.ingest(self.pr_url, max_prs)
        print(f"✅ Ingested {result['ingested']} PRs from repository")
        return f"Ingested {result['ingested']} PRs"

class DICLEvolve:
    def __init__(self, pr_url: str, ai_handler=None, args: list = None):
        self.pr_url = pr_url
        self.args = args or []
        self.ai_handler = ai_handler
        
    async def run(self):
        get_settings().set("enable_dicl", True)
        get_settings().set("config.publish_output", False)
        reviewer = PRReviewer(self.pr_url, args=self.args, ai_handler=self.ai_handler)
        await reviewer.run()
        
        # Print the review to terminal instead of publishing
        if hasattr(reviewer, 'prediction') and reviewer.prediction:
            print("\n" + "="*80)
            print("🧬 DICL Enhanced PR Review")
            print("="*80)
            print(reviewer.prediction)
            print("="*80)
        
        return "Enhanced review with learning"