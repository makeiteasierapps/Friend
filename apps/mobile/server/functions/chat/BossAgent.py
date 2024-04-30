import os
import tiktoken
from openai import OpenAI
import dspy
from dotenv import load_dotenv

class BossAgent:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BossAgent, cls).__new__(cls)
        return cls._instance

    def __init__(self, openai_key=None, model='gpt-3.5-turbo'):
        if not hasattr(self, 'is_initialized'):
            self.is_initialized = True
            self.openai_key = openai_key or self._load_openai_key()
            self.model = model if model == 'gpt-4-turbo' else 'gpt-3.5-turbo'
            self.lm = None
            self.client = dspy.OpenAI(api_key=self.openai_key)  
            self.openai_client = OpenAI(api_key=self.openai_key)
            self.user_analysis = ""

    def _load_openai_key(self):
        load_dotenv()
        return os.getenv('OPENAI_API_KEY')

    def _initialize_dspy(self):
        if self.lm is None:
            try:
                self.lm = dspy.OpenAI(model=self.model, api_key=self.openai_key)
                dspy.settings.configure(lm=self.lm)
            except Exception as e:
                print(f"Failed to initialize dspy: {e}")
                self.lm = None

    def summarize_moment(self, moment):
        self._initialize_dspy()
        if self.lm:
            generate_summary_prompt = dspy.ChainOfThought('content -> content_title, content_summary')
            prediction = generate_summary_prompt(content=moment['text'])
            return prediction.content_summary, prediction.content_title
        else:
            print("dspy is not initialized.")
            return None
   
    def pass_to_boss_agent(self, message_obj):
        new_user_message = message_obj['user_message']
        chat_history = message_obj['chat_history']

        new_chat_history = self.manage_chat(chat_history, new_user_message)

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=new_chat_history,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                stream_obj = {
                    'message_from': 'agent',
                    'content': chunk.choices[0].delta.content,
                    'type': 'stream',
                }
                yield stream_obj
    
    def manage_chat(self, chat_history, new_user_message):
        """
        Takes a chat object extracts x amount of tokens and returns a message
        object ready to pass into OpenAI chat completion
        """

        new_name = []
        token_limit = 2000
        token_count = 0
        for message in chat_history:
            if token_count > token_limit:
                break
            if message['message_from'] == 'user':
                token_count += self.token_counter(message['content'])
                new_name.append({
                    "role": "user",
                    "content": message['content'],
                })
            else:
                token_count += self.token_counter(message['content'])
                new_name.append({
                    "role": "assistant",
                    "content": message['content'],
                })

        new_name.append({
            "role": "user",
            "content": new_user_message,
        })
        
        return new_name
    
    def process_message(self, chat_id, user_message, chat_history):
        message_content = user_message['content']
        message_obj = {
            'user_message': message_content,
            'chat_history': chat_history
        }
        for response_chunk in self.pass_to_boss_agent(message_obj):
            response_chunk['chat_id'] = chat_id
            yield response_chunk

    def prepare_vector_response(self, query_results):
        text = []

        for item in query_results:
            if item['score'] > 0.4:
                print(item)
                text.append(item['text'])

        combined_text = ' '.join(text)
        project_query_instructions = f'''
        \nAnswer the users question based off of the knowledge base provided below, provide 
        a detailed response that is relevant to the users question.\n
        KNOWLEDGE BASE: {combined_text}
        '''
        return project_query_instructions
    
    def token_counter(self, message):
        """Return the number of tokens in a string."""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        
        tokens_per_message = 3
        num_tokens = 0
        num_tokens += tokens_per_message
        num_tokens += len(encoding.encode(message))
        num_tokens += 3  # every reply is primed with <|im_start|>assistant<|im_sep|>
        return num_tokens