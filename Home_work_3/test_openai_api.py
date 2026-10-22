from os import getenv

from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from openai import AuthenticationError, APIConnectionError, RateLimitError


def main():
    api_key = getenv("OPENAI_API_KEY")

    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        return

    try:
        model = ChatOpenAI(
            model="gpt-6-luna",
            temperature=0,
            max_tokens=20,
        )

        messages = [
            SystemMessage(
                content="You are a helpful assistant."
            ),
            HumanMessage(
                content="Reply with exactly: API key works!"
            ),
        ]

        response = model.invoke(messages)

        print("SUCCESS: API request completed.")
        print(f"Model response: {response.content}")
        print(f"Usage: {response.usage_metadata}")

    except AuthenticationError:
        print("ERROR: Authentication failed. Check your API key.")

    except RateLimitError:
        print(
            "ERROR: API rate limit or quota issue. "
            "Check your API usage and billing."
        )

    except APIConnectionError as error:
        print(f"ERROR: Could not connect to OpenAI API: {error}")

    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
