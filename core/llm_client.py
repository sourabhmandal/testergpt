import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from testergpt.settings import settings
from core.types import PRReviewResponse


def get_llm(model="gemini-2.5-pro", temperature=0.2):
    """Return a LangChain LLM instance with proper error handling"""
    if not settings.GPT_API_KEY or settings.GPT_API_KEY == "sk-YourAIKeyHere":
        raise ValueError(
            "Google API key is not configured. Please set GPT_API_KEY in your .env file"
        )

    try:
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.GPT_API_KEY,
            convert_system_message_to_human=True,
        )
    except Exception as e:
        logging.error(f"Failed to initialize LLM client: {e}")
        raise


def review_pr(diff: str) -> PRReviewResponse:
    """Send a diff to LLM and return structured JSON response"""
    if not diff or not diff.strip():
        raise ValueError("Diff content is empty or invalid")

    try:
        return flow_syntax_and_semantic_check(diff, model="gemini-2.5-pro")
    except Exception as e:
        logging.error(f"Error in review_pr: {e}")
        # Return a fallback response with proper structure
        fallback_response = PRReviewResponse(
            issues=[], summary=f"Error occurred during code review: {str(e)}"
        )
        return fallback_response


def tester_planner(diff: str) -> PRReviewResponse:
    """Send a diff to LLM and return structured JSON response"""
    if not diff or not diff.strip():
        raise ValueError("Diff content is empty or invalid")

    try:
        return flow_syntax_and_semantic_check(diff, model="gemini-2.5-pro")
    except Exception as e:
        logging.error(f"Error in review_pr: {e}")
        # Return a fallback response with proper structure
        fallback_response = PRReviewResponse(
            issues=[], summary=f"Error occurred during code review: {str(e)}"
        )
        return fallback_response
    
def flow_test_planner(diff: str, model="gemini-2.5-pro") -> PRReviewResponse:
    """Perform syntax and semantic analysis on code diff"""
    if not diff or not diff.strip():
        raise ValueError("Diff content is empty or invalid")

    try:
        llm = get_llm(model)

        # Create structured output LLM
        structured_llm = llm.with_structured_output(PRReviewResponse)

        template = """
        You are an AI code test case planner. Focus specifically on generating comprehensive test cases for the provided git diff.

        Diff:
        ```diff
        {diff}
        ```
        
        TEST CASE PLANNING INSTRUCTIONS:
        - Analyze all added/modified code (lines starting with '+')
        - Identify key functionalities and edge cases
        - Generate detailed test cases covering various scenarios
        - Include input data, expected outputs, and any setup/teardown steps
        - Ensure coverage of boundary conditions and error handling
        - Consider performance and security aspects where applicable
        
        For each test case, specify:
        - title: A concise title for the test case
        - description: A detailed description of what the test case covers
        - steps: Step-by-step instructions to execute the test case
        - expected_result: The expected outcome of the test case
        
        Provide a summary focusing on the overall testing strategy and coverage.
        """

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | structured_llm
        response = chain.invoke({"diff": diff})

        if not response:
            raise RuntimeError("Empty response from LLM")

        # Response is already a PRReviewResponse object from structured output
        return response

    except Exception as e:
        logging.error(f"Error in syntax_and_lint_check: {e}")
        # Return a fallback response with proper structure
        fallback_response = PRReviewResponse(
            issues=[],
            summary=f"Error occurred during syntax and semantic analysis: {str(e)}",
        )
        return fallback_response

def flow_syntax_and_semantic_check(
    diff: str, model="gemini-2.5-pro"
) -> PRReviewResponse:
    """Perform syntax and semantic analysis on code diff"""
    if not diff or not diff.strip():
        raise ValueError("Diff content is empty or invalid")

    try:
        llm = get_llm(model)

        # Create structured output LLM
        structured_llm = llm.with_structured_output(PRReviewResponse)

        template = """
        You are an AI code syntax and semantic analyzer. Focus specifically on syntax validation and semantic correctness of the provided git diff.

        Diff:
        ```diff
        {diff}
        ```
        
        SYNTAX AND SEMANTIC ANALYSIS INSTRUCTIONS:
        - Perform comprehensive syntax validation on all added/modified code (lines starting with '+')
        - Check for semantic correctness and logical consistency
        - Validate proper language-specific syntax rules
        - Identify potential runtime errors and type mismatches
        - Check for proper variable declarations and scope issues
        - Validate function/method signatures and return types
        - Ensure proper import statements and module usage
        - Check for undefined variables, functions, or classes
        - Validate proper exception handling patterns
        - Identify potential null/undefined reference errors
        
        LINTING CHECKS:
        - Code formatting and style consistency
        - Naming conventions (variables, functions, classes)
        - Proper indentation and whitespace usage
        - Missing or incorrect docstrings/comments
        - Unused imports or variables
        - Overly complex functions or expressions
        - Magic numbers or hardcoded values
        - Proper error handling practices
        
        LANGUAGE-SPECIFIC CHECKS:
        For Python:
        - PEP 8 compliance
        - Proper use of list comprehensions vs loops
        - Correct exception handling with try/except
        - Type hints usage and correctness
        - Proper use of f-strings vs format()
        
        For JavaScript/TypeScript:
        - ESLint rule compliance
        - Proper async/await usage
        - Type safety (for TypeScript)
        - Proper Promise handling
        - Variable declaration best practices (const/let)
        
        For each issue found, specify:
        - type: "error" for syntax errors, "warning" for potential issues, "suggestion" for style improvements
        - line: Use the NEW file line number from diff hunks for added/modified lines
        - message: Clear description focusing on syntax/semantic issue
        - severity: "high" for syntax errors, "medium" for semantic issues, "low" for style suggestions
        - file: Extract file path from diff headers, removing 'a/' or 'b/' prefixes
        
        CRITICAL FILE PATH EXTRACTION:
        - From "diff --git a/path/to/file.py b/path/to/file.py" → use "path/to/file.py"
        - From "+++ b/path/to/file.py" → use "path/to/file.py"
        - From "--- a/path/to/file.py" → use "path/to/file.py"
        - Remove any 'a/' or 'b/' prefixes from file paths
        
        CRITICAL LINE NUMBER EXTRACTION:
        - For issues on added lines (starting with +), use the line number from the NEW file
        - Parse diff hunk headers like @@ -old_start,old_count +new_start,new_count @@
        - Count line numbers from the new_start position for added lines
        - Only report line numbers for lines that actually exist in the diff
        
        Provide a summary focusing on syntax correctness, semantic validity, and code quality improvements.
        """

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | structured_llm
        response = chain.invoke({"diff": diff})

        if not response:
            raise RuntimeError("Empty response from LLM")

        # Response is already a PRReviewResponse object from structured output
        return response

    except Exception as e:
        logging.error(f"Error in syntax_and_lint_check: {e}")
        # Return a fallback response with proper structure
        fallback_response = PRReviewResponse(
            issues=[],
            summary=f"Error occurred during syntax and semantic analysis: {str(e)}",
        )
        return fallback_response
