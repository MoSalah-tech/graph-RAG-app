import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.agents.finance_agent import build_agent

def main():
    agent = build_agent()
    config = {"configurable": {"thread_id": "test-1"}}

    questions = [
        "What is Apple's ticker?",
        "What companies does Apple have relationships with?",
        "Is there a path between Apple and Caterpillar?",
        "Show me the top 5 companies by number of relationships.",
    ]

    for q in questions:
        print(f"\n{'='*60}\nQ: {q}\n{'='*60}")
        result = agent.invoke(
            {"messages": [("user", q)]},
            config=config,
        )
        print(f"A: {result['messages'][-1].content}")

if __name__ == "__main__":
    main()