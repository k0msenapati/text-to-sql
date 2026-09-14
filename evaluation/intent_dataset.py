from dataclasses import dataclass


@dataclass
class IntentTestCase:
    id: str
    question: str
    expected_intent: str
    category: str


INTENT_BENCHMARK_CASES: list[IntentTestCase] = [
    # --- DATA QUERIES ---
    IntentTestCase(
        id="DATA-01",
        question="List all customers who live in Canada.",
        expected_intent="data_query",
        category="Data Filtering",
    ),
    IntentTestCase(
        id="DATA-02",
        question="What is the total revenue from all completed orders?",
        expected_intent="data_query",
        category="Data Aggregation",
    ),
    IntentTestCase(
        id="DATA-03",
        question="Find the top 5 most expensive products and their prices.",
        expected_intent="data_query",
        category="Data Sorting & Limit",
    ),
    IntentTestCase(
        id="DATA-04",
        question="Which customers placed more than 3 orders?",
        expected_intent="data_query",
        category="Data Grouping & Having",
    ),
    IntentTestCase(
        id="DATA-05",
        question="Show customer names along with the items they purchased.",
        expected_intent="data_query",
        category="Data Join",
    ),
    IntentTestCase(
        id="DATA-06",
        question="How many 5-star reviews does each product have?",
        expected_intent="data_query",
        category="Data Aggregation",
    ),

    # --- METADATA QUERIES ---
    IntentTestCase(
        id="META-01",
        question="What tables are present in this database?",
        expected_intent="metadata_query",
        category="Table Listing",
    ),
    IntentTestCase(
        id="META-02",
        question="What columns does the orders table have and what are their types?",
        expected_intent="metadata_query",
        category="Column Inspection",
    ),
    IntentTestCase(
        id="META-03",
        question="Show me the full database schema.",
        expected_intent="metadata_query",
        category="Schema Overview",
    ),
    IntentTestCase(
        id="META-04",
        question="What are the foreign key relationships between customers and orders?",
        expected_intent="metadata_query",
        category="Relationship Inspection",
    ),
    IntentTestCase(
        id="META-05",
        question="Is there an email column in the customers table?",
        expected_intent="metadata_query",
        category="Column Existence",
    ),
    IntentTestCase(
        id="META-06",
        question="What constraints exist on the reviews rating column?",
        expected_intent="metadata_query",
        category="Constraint Inspection",
    ),

    # --- AMBIGUOUS QUERIES ---
    IntentTestCase(
        id="AMBI-01",
        question="Show me that thing.",
        expected_intent="ambiguous_query",
        category="Vague Pronoun",
    ),
    IntentTestCase(
        id="AMBI-02",
        question="What about the others?",
        expected_intent="ambiguous_query",
        category="Missing Context",
    ),
    IntentTestCase(
        id="AMBI-03",
        question="Details please.",
        expected_intent="ambiguous_query",
        category="Underspecified Command",
    ),
    IntentTestCase(
        id="AMBI-04",
        question="Can you check?",
        expected_intent="ambiguous_query",
        category="Incomplete Request",
    ),
    IntentTestCase(
        id="AMBI-05",
        question="Status?",
        expected_intent="ambiguous_query",
        category="Single Word Prompt",
    ),
    IntentTestCase(
        id="AMBI-06",
        question="Filter by the active one.",
        expected_intent="ambiguous_query",
        category="Ambiguous Entity Reference",
    ),

    # --- OUT OF SCOPE QUERIES ---
    IntentTestCase(
        id="OOS-01",
        question="What is the capital of France?",
        expected_intent="out_of_scope_query",
        category="World Knowledge",
    ),
    IntentTestCase(
        id="OOS-02",
        question="Write a Python function to compute the Fibonacci sequence.",
        expected_intent="out_of_scope_query",
        category="General Programming",
    ),
    IntentTestCase(
        id="OOS-03",
        question="Can you write a poem about autumn leaves?",
        expected_intent="out_of_scope_query",
        category="Creative Writing",
    ),
    IntentTestCase(
        id="OOS-04",
        question="How do I make chocolate chip cookies from scratch?",
        expected_intent="out_of_scope_query",
        category="General Advice",
    ),
    IntentTestCase(
        id="OOS-05",
        question="Who won the FIFA World Cup in 2022?",
        expected_intent="out_of_scope_query",
        category="Sports Facts",
    ),
    IntentTestCase(
        id="OOS-06",
        question="Explain how the theory of general relativity works.",
        expected_intent="out_of_scope_query",
        category="Science & Physics",
    ),
]
