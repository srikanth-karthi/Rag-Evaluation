
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv
from cohere import Client as CohereClient
from astrapy import DataAPIClient

load_dotenv()


class DirectRAGTester:


    def __init__(self):

        cohere_keys = [
            os.getenv('COHERE_API_KEY_1'),
            os.getenv('COHERE_API_KEY_2')
        ]
        self.cohere = CohereClient(api_key=cohere_keys[0])

        # Initialize Astra DB
        client = DataAPIClient(os.getenv('ASTRA_DB_APPLICATION_TOKEN'))

        # Get database with namespace
        namespace = os.getenv('ASTRA_DB_NAMESPACE') or 'default_keyspace'
        self.db = client.get_database(
            api_endpoint=os.getenv('ASTRA_DB_API_ENDPOINT'),
            keyspace=namespace
        )

        # Get collection
        self.collection = self.db.get_collection("portfolio")


        self.groq_keys = [
            os.getenv('GROQ_API_KEY_1'),
            os.getenv('GROQ_API_KEY_2')
        ]

        self.results = []

        print("Database and LLM connections established")

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Cohere"""
        response = self.cohere.embed(
            texts=[text],
            model="embed-english-v2.0",
            input_type="search_document"
        )
        return response.embeddings[0]

    def retrieve_documents(self, query: str, limit: int = 6) -> Tuple[List[Dict], List[int], List[float]]:
        """
        Retrieve documents from vector DB

        Returns:
            (documents, doc_ids, scores)
        """
        # Get query embedding
        query_vector = self.get_embedding(query)

        # Query vector DB
        cursor = self.collection.find(
            {},
            sort={"$vector": query_vector},
            limit=limit,
            projection={"metadata": True, "description": True},
            include_similarity=True
        )

        documents = list(cursor)


        doc_ids = [doc['metadata']['id'] for doc in documents]
        scores = [doc.get('$similarity', 0.0) for doc in documents]

        return documents, doc_ids, scores

    def generate_answer(self, query: str, documents: List[Dict]) -> str:


        # Build context from retrieved documents
        doc_context = "\n".join([
            f"• {doc['metadata']['title']}: {doc['description']}"
            for doc in documents
        ])

        # Build prompt (same as your API)
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI assistant speaking on behalf of Srikanth for his Portfolio App.

Your responses should sound like Srikanth is directly answering the question.

CRITICAL RULES:
1. ONLY use information from the provided CONTEXT section below
2. NEVER make up, invent, or hallucinate any information
3. If the context doesn't contain the answer, you MUST say: "I'm sorry, I don't have that information available right now."
4. DO NOT create fake article titles, project names, or any other details
5. Always respond in first-person ("I", "my", "me")

Response Guidelines:
- Keep answers short, concise, and factual
- Use minimal markdown for emphasis only when needed
- Maintain a friendly and professional tone
- Stick strictly to the facts provided in the context

What you have access to:
- Srikanth's education, experience, skills, certifications
- Contact information and social profiles
- Volunteer work and achievements
- ONLY what is explicitly provided in the context

What you CANNOT do:
- Create fictional content or details
- Assume information not in the context
- Make up article titles, project descriptions, or experiences
- Provide information beyond what's explicitly stated

Formatting Rule for Highlighted Words:
- Always bold category headings
- Always bold important words, sentences, or content that should stand out
- To bold, enclose the word/sentence with ** on both sides.
  Example: **Programming languages**

Formatting Rule for Links:
- Always return links in the format: <https://example.com>

BEFORE RESPONDING, ASK YOURSELF:
"Is every single detail in my response explicitly written in the context?"
If NO, remove those details immediately.

START CONTEXT
{doc_context}
END CONTEXT

Remember: If it's not in the context above, don't make it up. Simply say you don't have that information.
"""
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Call Groq API
        import requests

        for api_key in self.groq_keys:
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']

            except Exception as e:
                print(f"Groq API error: {e}")
                continue

        return "Error: Could not generate answer"

    def test_query(self, query: str) -> Dict:
        """Test a single query through the RAG pipeline"""

        print(f"\nQuery: {query}")

        start_time = time.time()

        try:
            # Step 1: Retrieve documents
            documents, doc_ids, scores = self.retrieve_documents(query)
            print(f"Retrieved docs: {doc_ids[:3]} (top score: {scores[0]:.3f})")

            # Step 2: Generate answer
            answer = self.generate_answer(query, documents)

            response_time = time.time() - start_time

            print(f"Response time: {response_time:.2f}s")
            print(f"Answer: {answer[:100]}...")

            return {
                "query": query,
                "generated_answer": answer,
                "retrieved_contexts": doc_ids,
                "retrieval_scores": scores,
                "response_time": response_time,
                "success": True,
                "error": None
            }

        except Exception as e:
            response_time = time.time() - start_time
            print(f"Error: {str(e)}")

            return {
                "query": query,
                "generated_answer": None,
                "retrieved_contexts": [],
                "retrieval_scores": [],
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }

    def test_queries(self, queries_file: str):
        """Test all queries from JSON file"""

        print("=" * 80)
        print("DIRECT RAG TESTING")
        print("=" * 80)
        print(f"\nQueries File: {queries_file}\n")

        # Load queries
        with open(queries_file, 'r') as f:
            queries_data = json.load(f)

        total = len(queries_data)
        print(f"Testing {total} queries...")
        print("=" * 80)

        # Test each query
        for i, item in enumerate(queries_data, 1):
            query = item['query']

            print(f"\n[{i}/{total}]", end=" ")

            result = self.test_query(query)
            self.results.append(result)

            # Small delay
            if i < total:
                time.sleep(1)

        print("\n" + "=" * 80)
        print("Testing complete")

    def generate_report(self, output_dir: str = "./rag_results"):
        """Generate test report"""

        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("\n" + "=" * 80)
        print("TEST REPORT")
        print("=" * 80)

        # Calculate stats
        total = len(self.results)
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]

        success_rate = (len(successful) / total * 100) if total > 0 else 0
        avg_response_time = sum(r['response_time'] for r in successful) / len(successful) if successful else 0

        if successful and successful[0]['retrieval_scores']:
            avg_top_score = sum(r['retrieval_scores'][0] for r in successful if r['retrieval_scores']) / len(successful)
        else:
            avg_top_score = 0

        print(f"\nOVERALL STATISTICS")
        print("-" * 80)
        print(f"  Total Queries:        {total}")
        print(f"  Successful:           {len(successful)}")
        print(f"  Failed:               {len(failed)}")
        print(f"  Success Rate:         {success_rate:.1f}%")
        print(f"  Avg Response Time:    {avg_response_time:.3f}s")
        print(f"  Avg Top Retrieval:    {avg_top_score:.3f}")

        # Save results
        output_file = os.path.join(output_dir, f"evaluation_results_{timestamp}.json")

        formatted_results = []
        for result in self.results:
            formatted_results.append({
                "query": result['query'],
                "generated_answer": result['generated_answer'],
                "retrieved_contexts": result['retrieved_contexts'],
                "retrieval_scores": result['retrieval_scores'],
                "response_time": result['response_time'],
                "success": result['success'],
                "error": result.get('error')
            })

        with open(output_file, 'w') as f:
            json.dump(formatted_results, f, indent=2)

        print(f"\nResults saved to: {output_file}")

        # Save readable report
        report_file = os.path.join(output_dir, f"readable_report_{timestamp}.txt")
        self._save_readable_report(report_file)

        print(f"Report saved to: {report_file}")

        # Show failed queries
        if failed:
            print(f"\nFAILED QUERIES ({len(failed)})")
            print("-" * 80)
            for result in failed:
                print(f"  - {result['query'][:60]}...")
                print(f"    Error: {result['error']}")

        print("=" * 80)

    def _save_readable_report(self, report_file: str):
        """Save human-readable report"""

        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("RAG TEST REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for i, result in enumerate(self.results, 1):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"[{i}/{len(self.results)}] QUERY\n")
                f.write(f"{'=' * 80}\n\n")

                f.write(f"Query: {result['query']}\n\n")

                if result['success']:
                    f.write(f"Status: SUCCESS\n")
                    f.write(f"Response Time: {result['response_time']:.3f}s\n")

                    if result['retrieved_contexts']:
                        f.write(f"Retrieved Docs: {result['retrieved_contexts']}\n")
                        if result['retrieval_scores']:
                            f.write(f"Top Score: {result['retrieval_scores'][0]:.3f}\n")

                    f.write(f"\nGenerated Answer:\n{'-' * 80}\n")
                    f.write(f"{result['generated_answer']}\n")
                    f.write(f"{'-' * 80}\n")
                else:
                    f.write(f"Status: FAILED\n")
                    f.write(f"Error: {result['error']}\n")
                    f.write(f"Response Time: {result['response_time']:.3f}s\n")

            f.write(f"\n\n{'=' * 80}\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")


def main():
    """Main execution"""

    # Configuration
    QUERIES_FILE = "./portfolio-data/portfolio_evaluation_queries.json"

    # Initialize tester
    tester = DirectRAGTester()

    # Test all queries
    tester.test_queries(QUERIES_FILE)

    # Generate report
    tester.generate_report()

    print("\nDone! Check the rag_results/ folder for results.\n")


if __name__ == "__main__":
    main()
