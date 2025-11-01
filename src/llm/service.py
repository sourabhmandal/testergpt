
import logging
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.config.env import settings
from src.llm.prompts import FLOW_SYNTAX_AND_SEMANTIC_CHECK_PROMPT
from src.llm.types import ReviewCodeDiffRequest, ReviewCodeDiffResponse

logger = logging.getLogger(__name__)

class LLMService:
    llm = None

    def __init__(self, model="gemini-2.5-pro", temperature=0.2):
        if self.llm is None:
            if not settings.GPT_API_KEY or settings.GPT_API_KEY == "sk-YourAIKeyHere":
                raise ValueError("Google API key missing. Please set GPT_API_KEY in your .env file")
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=model,
                    temperature=temperature,
                    google_api_key=settings.GPT_API_KEY,
                    convert_system_message_to_human=True,
                )
            except Exception as e:
                logging.error(f"Failed to initialize LLM client: {e}")
                raise
    
    def review_code_diff(self, code_diff_request: ReviewCodeDiffRequest) -> ReviewCodeDiffResponse:
        try:
            if not code_diff_request.diff.strip():
                raise ValueError("Diff content is empty or invalid")
            structured_llm = self.llm.with_structured_output(ReviewCodeDiffResponse)
            prompt = ChatPromptTemplate.from_template(FLOW_SYNTAX_AND_SEMANTIC_CHECK_PROMPT)
            chain = prompt | structured_llm
            response = chain.invoke({"diff": code_diff_request.diff})

            print(response.model_dump_json())
            if not response:
                raise RuntimeError("Empty response from LLM")
            return response
        except Exception as e:
            logger.error(f"Error: review_code_diff : {e}")
            raise
