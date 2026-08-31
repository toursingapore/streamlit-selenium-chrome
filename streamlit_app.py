import nest_asyncio
nest_asyncio.apply() #Enable asyncio in the main thread and Run the asynchronous function
import asyncio

import streamlit as st
from bs4 import BeautifulSoup
import time
from pyngrok import ngrok
import html2text
import requests, json
from typing import Any, Dict, List, Optional, Type, Union, Callable
from concurrent.futures import ThreadPoolExecutor
import uuid
import os, sys, subprocess
import base64
from base64 import b64encode

from prefect import task, flow
from prefect.schedules import Cron

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"]


def send_email_notification_mailtrap(email_receiver, html_notify):
	global mailtrap_api_key
	mailtrap_api_key = st.secrets["MAILTRAP_API_KEY"]

	import smtplib
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText   
	from datetime import datetime	

	subject = "Notification for you"
	sender  = "hello@demomailtrap.co"   # keep default
	# Create proper MIME container
	msg = MIMEMultipart("alternative")
	msg["Subject"] = subject
	msg["From"]    = sender
	msg["To"]      = email_receiver
	# Attach HTML body
	html_part = MIMEText(html_notify, "html")
	msg.attach(html_part)
	smtp_server = "live.smtp.mailtrap.io"
	smtp_port   = 587
	username    = "api"
	password    = mailtrap_api_key
	with smtplib.SMTP(smtp_server, smtp_port) as server:
		server.starttls()
		server.login(username, password)
		server.sendmail(sender, email_receiver, msg.as_string())
	st.write(f"Email sent via SMTP to {email_receiver}")

def run_function_in_background_use_threadPool(
	function_name: Callable,
	*args,
	wait_until_finish: bool = False,
	timeout: Optional[float] = None,
	**kwargs
) -> Any:
	#html_notify = f'<p>No reply - starting run function in background use threadPool</p>'
	#email_receiver = "ahai72160@gmail.com" #chỉ gửi tới được email đã reg acc
	#send_email_notification_mailtrap(email_receiver, html_notify)

	#C1; khó truyền tham số args và lấy return values 
	#thread = threading.Thread(target=function_name, daemon=True)
	#thread.start()
	#st.write(f"Started background task: {function.__name__}")
	#thread.join() #Optional; block UI để chờ thread chạy xong
	#st.write(f"Thread completed function name {function_name}")
		
	#C2; Cái này tốt hơn threading ở trên vì sử dụng function with args or not args
	executor = ThreadPoolExecutor(max_workers=1)
	future = executor.submit(function_name, *args, **kwargs)
	if not wait_until_finish:
		result = future
		return result
	try:
		result = future.result(timeout=timeout)
		return result
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		errorInfo = f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}"
		html_notify = f'<p>No reply - {errorInfo}</p>'
		email_receiver = "ahai72160@gmail.com" #chỉ gửi tới được email đã reg acc
		send_email_notification_mailtrap(email_receiver, html_notify)
	finally:
		executor.shutdown(wait=False)
#1. Chạy background, không chờ
#future = run_function_in_background_use_threadPool(my_function, arg1, arg2)
#2. Chạy background và chờ
#future = run_function_in_background_use_threadPool(my_function, arg1, arg2, wait_until_finish=True)
#3. Chạy background và chờ có timeout
#future = run_function_in_background_use_threadPool(my_function, arg1, arg2, timeout=10)

def run_command_line(command, returnValue=False, ShowError=True):
	whole_text = ""  # Initialize whole_text
	try:
		# Run the command and capture the output
		output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
		output = output.decode('utf-8')
		# Split the output into a list of lines
		lines = output.split('\n')
		# Write each line separately
		for line in lines:
			if returnValue:
				whole_text += line + '\n'  # Add a newline for better formatting
			else:
				st.write(line)                
		if returnValue:
			return whole_text  # Return the whole text if requested
	except subprocess.CalledProcessError as e:
		if ShowError:
			st.write(f"An error occurred: {e.output.decode('utf-8')}")      

def delete_files_in_temp_folder(defaultFolder='/tmp', Filename_extension='jpg'):
	#Get list of files im temp folder, then Delete all temp files
	import glob
	#st.write(glob.glob('/tmp/*.*'))                    
	#for f in glob.glob('/tmp/*.jpg'):    
	for f in glob.glob(f'{defaultFolder}/*.{Filename_extension}'):
		os.remove(f)  

def Convert_image_local_path_toBase64(image_path):
	if not image_path or not isinstance(image_path, (str, os.PathLike)):
		return None  # không có ảnh thì bỏ qua
	if not os.path.exists(image_path):
		raise FileNotFoundError(f"Image not found: {image_path}")
	with open(os.path.abspath(image_path), 'rb') as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')

def chatbot_vision_by_groq(prompt, image_path=None, model="meta-llama/llama-4-scout-17b-16e-instruct"):
	try:		
		if not GROQ_API_KEY:
			raise ValueError("Missing GROQ_API_KEY environment variable")

		base64_image = None
		if image_path:
			base64_image = Convert_image_local_path_toBase64(image_path)

		user_content = [
			{
				"type": "text",
				"text": prompt
			}
		]
		if base64_image:
			user_content.append({
				"type": "image_url",
				"image_url": {
					"url": f"data:image/jpeg;base64,{base64_image}"
				}
			})
		payload = {
			"model": model,
			"messages": [
				{
					"role": "system",
					"content": "You are an expert vision AI. Always respond in the same language as the user."
				},
				{
					"role": "user",
					"content": user_content
				}
			],
			"temperature": 1.0,
			"max_completion_tokens": 1024,
			"top_p": 1.0,
			"stream": False
		}
		headers = {
			"Authorization": f"Bearer {GROQ_API_KEY}",
			"Content-Type": "application/json"
		}
		response = requests.post(
			"https://api.groq.com/openai/v1/chat/completions",
			headers=headers,
			json=payload,
			timeout=60
		)
		if response.status_code != 200:
			return f"API Error {response.status_code}: {response.text}"
		data = response.json()
		if "choices" not in data:
			return f"Invalid response: {data}"
		return data["choices"][0]["message"]["content"]
	except Exception as e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		error = f"An error occurred: {e} - File: {fname} - Line: {exc_tb.tb_lineno}"
		return error




def myrun():
	st.set_page_config(
		page_title="Web scraping on Streamlit Cloud", 
		page_icon=":star:",
	)     

	with st.sidebar:
		#Navigate to element in current page
		st.markdown(f"<a href='#youtube-view'>YOUTUBE VIEW</a>", unsafe_allow_html=True)
		st.markdown(f"<a href='#web-scraper'>WEB SCRAPER</a>", unsafe_allow_html=True)
		st.markdown(f"<a href='#python-workflow-pipelines'>PYTHON WORKFLOW PIPELINES</a>", unsafe_allow_html=True)
		st.markdown(f"<a href='#connect-postgressql'>CONNECT POSTGRESSQL</a>", unsafe_allow_html=True)
		st.markdown(f"<a href='#colab-test-code'>COLAB TEST CODE</a>", unsafe_allow_html=True)

	st.markdown(
	"""
	## Web scraping on Streamlit Cloud
	"""
	)

	with st.container(border=True):   
		st.write("## YOUTUBE VIEW")
		user_input = st.text_area("Enter URL of YouTube video", value='https://www.youtube.com/watch?v=zo-DreoLioM\nhttps://www.youtube.com/watch?v=r-XPZMk1ypM', height=200)
		#Append keywords to array and remove whitespace dư, empty line 
		user_input_arr = [line.strip() for line in user_input.split('\n') if line.strip()]  

		button = st.button("SUBMIT", type="primary" , key="24dfdlk5vb235")
		if button:
			for user_input in user_input_arr:
				try:			
					#C1; view youtube embeded video
					if 'youtube.com' in user_input:
						st.write('> view video youtube url directly')
						youtube_video_url = user_input
						if 'shorts' in youtube_video_url or 'live' in youtube_video_url:
							x = youtube_video_url.split("/")
							video_id = x[-1]
							st.write(f'Shorts videoID: {video_id}')
						else:
							x = youtube_video_url.split("=")
							video_id = x[1]
							st.write(f'videoID: {video_id}')

						#embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1" #autoplay ko tính view
						embed_url = f"https://www.youtube.com/embed/{video_id}"
						st.components.v1.iframe(embed_url,height=500)
					else:
						#C1; view mp4 url directly
						st.write('> view mp4 url directly')
						mp4_url = user_input
						st.video(mp4_url)
					st.write("---")					
				except Exception as e:
					exc_type, exc_obj, exc_tb = sys.exc_info()
					fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
					#st.write(exc_type, fname, exc_tb.tb_lineno)
					st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")   

	with st.container(border=True):   
		st.write("## PYTHON WORKFLOW PIPELINES")

		button = st.button("SUBMIT", type="primary" , key="24dfdas5vb235")
		if button:
			try:
				st.write('Hello world')

				def test_workflow_func():
					@task(retries=1, retry_delay_seconds=5, timeout_seconds=300)
					def task_1(param):
						st.write("Run task 1 already")
						result = param + 6
						return result

					@task
					def task_2(param):
						st.write("Result is", param)

					@flow
					def my_flow():
						param = 2
						# Gọi task với return_state=True để lấy trạng thái
						state_1 = task_1(param, return_state=True)

						# Kiểm tra trạng thái
						if state_1.is_completed():
							st.write("Task 1 is success")
							result = state_1.result()
						else:
							st.write("Task 1 is failed")
							result = None

						if result:
							task_2(result)

					my_flow() #chạy one time only 

					_ = """
					# Schedule run workflow on server
					my_flow.serve(
						name="daily-6am-flow",
						schedule=Cron("0 6 * * *") #Lên lịch: chạy mỗi ngày lúc 6h sáng - phút giờ ngày tháng thứ (0 6 * * * = 6:00 hàng ngày)
						#schedule=Interval(interval=datetime.timedelta(seconds=5))#Lên lịch: chạy mỗi 5 giây
					)	
					_ = """			

				test_workflow_func()

			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				#st.write(exc_type, fname, exc_tb.tb_lineno)
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  

	with st.container(border=True):   
		st.write("## CONNECT POSTGRESSQL")

		button = st.button("SUBMIT", type="primary" , key="24dfdas5235")
		if button:
			try:
				st.write('Hello world') 

				import pandas as pd
				from sqlalchemy import create_engine, text
				from sqlalchemy.exc import SQLAlchemyError

				@st.cache_resource
				def get_engine():
					DATABASE_URL = st.secrets["DATABASE_URL"]
					return create_engine(DATABASE_URL)
				engine = get_engine()    

				#Case1; Load existing table into a Pandas DataFrame
				table_name = "my_table_1"  
				df = pd.read_sql_table(table_name, con=engine)
				st.write(df)        

				#List all column names
				#column_names = df.columns.tolist()
				#st.write(column_names)

				#Lấy all values tại cột và chuyển nó thành list, sau đó có thể merge thành 1 bảng mới
				title_df = df["Title video"].reset_index(drop=True)
				st.write(title_df)
				desc_df = df["Desc video"].reset_index(drop=True)
				st.write(desc_df)

				#Create a list of column name filename
				delete_files_in_temp_folder("mp4")
				delete_files_in_temp_folder("csv")               
				emailpcloud = st.secrets["EMAILPCLOUD"]
				passpcloud = st.secrets["PASSPCLOUD"]
				folderidpcloud = '28474967031'
				video_path_arr = download_all_files_in_folder_pcloud(emailpcloud, passpcloud, folderidpcloud)
				#st.write(video_path_arr)
				df_table = pd.DataFrame({
					'filename': pd.Series(video_path_arr),
				})
				#st.dataframe(df_table) 
				sorted_filename_df = df_table.sort_values(by='filename', ascending=True).reset_index(drop=True)
				st.write(sorted_filename_df)

				#Create a list of publish time
				publish_time_arr = [
					"2025-11-15T14:00:00Z",
					"2025-11-15T12:00:00Z",
				]
				# Auto-fill missing rows with blank
				total_rows = len(sorted_filename_df) #Example totals rows is 11
				publish_time_auto_fill_arr += [""] * (total_rows - len(publish_time_arr))

				publish_time_df = pd.DataFrame({
					#'publish_time': pd.Series(publish_time_arr), #if empty row fill NULL
					'publish_time': pd.Series(publish_time_auto_fill_arr), #Auto-fill missing rows with blank
				})
				#st.dataframe(publish_time_df)

				st.write('### Combined all') 
				df_table_arr = [sorted_filename_df, title_df, desc_df, publish_time_df]
				df_table_merged = pd.concat(
					df_table_arr,       # List or dictionary of DataFrames/Series to concatenate
					axis=1,             # 0 for vertical stacking (rows), 1 for horizontal stacking (columns)
					#ignore_index=True, # If True, reindexes the resulting DataFrame and ignore their column names, False will keep column names
					#keys=None,         # Adds hierarchical keys for identifying original DataFrames
					#join='outer'       # 'outer' for union, 'inner' for intersection of indices/columns
				) 
				st.write(df_table_merged)  
				# Export to CSV
				df_table_merged.to_csv("/tmp/videos_schedule.csv")              

			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				#st.write(exc_type, fname, exc_tb.tb_lineno)
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  

	with st.container(border=True):   
		st.write("## COLAB TEST CODE")

		button = st.button("SUBMIT", type="primary" , key="24dfdamk5235")
		if button:
			try:
				run_command_line("playwright install chromium")

				from scrapling.spiders import SiteToMarkdownSpider

				class DocsSpider(SiteToMarkdownSpider):
					name = "docs"
					start_urls = ["https://vnexpress.net/the-gioi"]
					allowed_domains = {"vnexpress.net"} # Limit chỉ lấy internal domain
					output_dir = "/tmp/docs_markdown"
					max_pages = 10

				result = DocsSpider().start()
				#result.items.to_jsonl("/tmp/docs.jsonl") # Lưu JSONL

				st.write(f"Crawl hoàn tất: {len(result.items)} pages")


				from langchain_core.documents import Document
				from langchain_text_splitters import RecursiveCharacterTextSplitter
				from langchain_core.embeddings import DeterministicFakeEmbedding
				from langchain_qdrant import QdrantVectorStore
				from langchain_openai import ChatOpenAI
				from langchain_core.prompts import ChatPromptTemplate
				from langchain_classic.chains import create_retrieval_chain, RetrievalQA
				from langchain_classic.chains.combine_documents import create_stuff_documents_chain


				# 1. Create LangChain Documents
				documents = []
				for i, item in enumerate(result.items, start=1):
					url = item["url"]
					title = item["title"]
					markdown = item["markdown"]
					#st.write(i, url, title, markdown)

					documents.append(
						Document(
							page_content=markdown,
							metadata={
								"url": url,
								"title": title,
							}
						)
					)
				#st.write(documents)
				st.write(f"Total documents: {len(documents)}")

				# 2. chunk Documents
				splitter = RecursiveCharacterTextSplitter(
					chunk_size=1000,
					chunk_overlap=150,
				)
				chunks = splitter.split_documents(documents)
				st.write(f"Total chunks: {len(chunks)}")

				# 3. Create Embedding
				embeddings = DeterministicFakeEmbedding(size=1536)

				# 4. Create vector store
				persist_directory = '/tmp/QdrantVectorStore_folder'
				# C1;
				_ = """
				texts = [doc.page_content for doc in chunks]
				metadatas = [doc.metadata for doc in chunks]
				vector_store = QdrantVectorStore.from_texts(
					texts=texts,
					metadatas=metadatas,
					embedding=embeddings,
					path=persist_directory,
					collection_name="my_collection"
				)
				_ = """
				#C2;
				vector_store = QdrantVectorStore.from_documents(
					documents=chunks,
					embedding=embeddings,
					path="/tmp/QdrantVectorStore_folder",
					collection_name="my_collection"
				)				
				st.write(f"Total vectors stored: {len(chunks)}")

				# 5. Create retriever
				retriever = vector_store.as_retriever(
					search_type="similarity",
					search_kwargs={"k": 5}
				)

				# Optional. test query trước
				#query = "Tình hình chiến sự thế giới hiện nay?"
				#docs = retriever.invoke(query)
				#for doc in docs:
				#	st.write(doc.page_content)
				#	st.write(doc.metadata)

				# 6. Setup LLM
				llm = ChatOpenAI(
					base_url="https://api.groq.com/openai/v1",
					api_key=GROQ_API_KEY,
					model="meta-llama/llama-4-scout-17b-16e-instruct",  #max Context window=131000
					temperature=0.3,
					timeout=60.0,
					max_tokens=8000,
					max_retries=0,
				)

				# 7. Setup Prompt
				prompt = ChatPromptTemplate.from_template("""
Trả lời bằng tiếng Việt.
Dùng thông tin trong CONTEXT.
Nếu không có thông tin, hãy nói không biết.

CONTEXT:
{context}

QUESTION:
{input}
""")

				# 8. Create Chain
				qa_chain = create_stuff_documents_chain(llm, prompt)
				rag_chain = create_retrieval_chain(retriever, qa_chain)

				# 9 Query
				query = "Tình hình chiến sự thế giới hiện nay?"
				result = rag_chain.invoke(
					{
						"input": query
					}
				)
				answer = result["answer"]
				st.write(answer)

				st.subheader("Nguồn")
				for doc in result["context"]:
					st.write(doc.metadata["url"])


				st.write(heoquay)


				st.write('Hello world') 

				from langchain_mcp_adapters.client import MultiServerMCPClient
				from langchain.agents import create_agent
				from langchain_openai import ChatOpenAI
				from langchain_core.tools import tool

				@tool
				def fetch_webpage(url: str) -> list:
					"""Fetch and extract readable text content from a webpage URL."""
					try:
						headers = {
							'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
						}
						response = requests.get(url, headers=headers, timeout=30)
						response.raise_for_status()
						soup = BeautifulSoup(response.content, 'html.parser')
						
						# Remove unwanted elements
						for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
							element.decompose()
						
						# Get main content
						text = soup.get_text(separator='\n', strip=True)
						lines = [line.strip() for line in text.splitlines() if line.strip()]
						clean_text = '\n'.join(lines)
						clean_text = clean_text[:15000]
						
						# CHUẨN HÓA OUTPUT theo MCP format: List[Dict] với type, text, id
						return [{
							"type": "text",
							"text": clean_text,
							"id": f"lc_{uuid.uuid4()}"
						}]
					except Exception as e:
						# CHUẨN HÓA OUTPUT cả khi lỗi
						return [{
							"type": "text",
							"text": f"Error fetching URL: {str(e)}",
							"id": f"lc_{uuid.uuid4()}"
						}]

				async def myfunc(prompt):
					try:
						# Đường dẫn folder cho filesystem server
						mcp_server_folder_path = "/tmp"

						# Connect to multiple MCP servers with MultiServerMCPClient (auto close all session after done)
						mcp_servers_config = {
							"sequential-thinking": {  # think logic lâu, dùng complex actions
								"transport": "stdio",
								"command": "npx",
								"args": [
									"-y", 
									"@modelcontextprotocol/server-sequential-thinking"
								]
							},						
							"filesystem": {
								"transport": "stdio",
								"command": "npx",
								"args": [
									"-y",
									"@modelcontextprotocol/server-filesystem",
									mcp_server_folder_path
								]
							},
							"memory": {
								"transport": "stdio",
								"command": "npx",
								"args": [
									"-y", 
									"@modelcontextprotocol/server-memory"
								]
							},
						}
						client = MultiServerMCPClient(
							connections=mcp_servers_config,
							handle_tool_errors=True
						)

						# 1. Fetch all tools from the connected MCP servers one time only and avoid overload memory for multiple connections
						st.write("Connecting to MCP servers...")
						mcp_tools = await client.get_tools()
						
						#tools = mcp_tools
						tools = mcp_tools + [fetch_webpage] #kết hợp tool tự tạo chuẩn output mcp

						st.write(f"Loaded {len(tools)} tools:")
						#st.write(tools)
						#for i, tool in enumerate(tools, start=1):
						#	st.write(f"{i}.{tool.name}: {tool.description}")
						
						# 2. Set up your LLM - dùng init_chat_model hoặc ChatOpenAI
						llm = ChatOpenAI(
							#base_url="https://integrate.api.nvidia.com/v1",
							#api_key=NVIDIA_API_KEY,
							#model="qwen/qwen3.5-122b-a10b", #Lưu ý phải là llm vision mới worked
							#base_url="https://zenmux.ai/api/v1",
							#api_key=ZENMUX_API_KEY,
							#model="stepfun/step-3.7-flash-free",
							base_url="https://api.groq.com/openai/v1",
							api_key=GROQ_API_KEY,
							model="openai/gpt-oss-20b",
							#model="openai/gpt-oss-120b",
							temperature=0.3,
							timeout=60.0, # timeout seconds with type float number
							max_retries=2,
						)
						#Check LLM work or not 
						response = llm.invoke("Hello! Reply only: LLM is working")
						st.write("LLM Response:", response.content)						
						
						# 3. Create your agent
						agent = create_agent(llm, tools)
						response = await agent.ainvoke({
							"messages": [{"role": "user", "content": prompt}]
						})						
						#st.write(response)

						ToolMessage = response["messages"][-2]
						tool_answer = ToolMessage.content
						#st.write(tool_answer)
						for i, data_json in enumerate(tool_answer, start=1):
							st.write('Tool answer - ', data_json.get("text"))

						AIMessage = response["messages"][-1]
						final_answer = AIMessage.content
						return final_answer						
					except Exception as e:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  


				# Run the async function
				prompt = "List the files in the current directory, output table clear easy to understand."
				#prompt = "Summarize content in short this url https://vnexpress.net/haaland-hay-don-moi-ap-luc-cho-tuyen-anh-5096051.html "
				final_answer = asyncio.run(myfunc(prompt))
				st.write(final_answer)


				st.write(heoquay) 


				from cloakbrowser import ensure_binary, launch_async, launch_context_async, launch_persistent_context_async, launch, launch_context, launch_persistent_context
				from browser_use import Agent, Browser, BrowserConfig
				from browser_use.browser.profile import BrowserProfile
				from browser_use.llm import ChatOpenAI
				
				async def browser_use_func(task):
					# delete_files_in_temp_folder(Filename_extension="webm")
					# delete_files_in_temp_folder(Filename_extension="har")						
					try:
						record_har_path = '/tmp/file.har'
						screenshot_image_path = '/tmp/screenshot.png'
						record_video_dir = '/tmp'
						cookies_state_json_path = "/tmp/cookies_state.json"

						binary_path = ensure_binary()
						st.write(f"Custom chromium browser path: {binary_path}")

						config = BrowserConfig(
							headless=True,
							executable_path=binary_path,
							#storage_state=cookies_state_json_path,
							#stealth=True,
							#user_agent=user_agent,
							viewport={"width": 1280, "height": 720},
							locale="en-US",
							timezone_id="America/New_York",
							geolocation={"longitude": 12.492507, "latitude": 41.889938},
							permissions=["geolocation", "clipboard-read", "clipboard-write"],
							#extra_http_headers=extra_http_headers,
							ignore_https_errors=True,
							record_video_dir=record_video_dir,
							record_video_size={"width": 1280, "height": 720},
							record_har_path=record_har_path,
							slow_mo=100, # quan trọng: giúp “human-like”
						)

						browser = Browser(config=config)
						llm = ChatOpenAI(
							base_url="https://integrate.api.nvidia.com/v1",
							api_key=NVIDIA_API_KEY,
							model="meta/llama-4-maverick-17b-128e-instruct", #Lưu ý phải là llm vision mới worked
							max_retries=2,
						)

						agent = Agent(
							task=task,
							llm=llm,
							browser=browser,
							max_steps=10, # Max 10 step then quit, nếu ko nó chạy hooài luôn - QUAN TRỌNG
						)
						results = await agent.run()
						st.write(results)

						# 1. Print total steps taken
						st.write(f"Total Steps: {results.number_of_steps()}")
						# 2. Print the final result text
						st.write(f"Final Result: {results.final_result()}")
						# 3. Iterate and print the individual action history per step
						for i, step in enumerate(results.history):
							st.write(f"Step {i+1}: {step.model_output.action}")

						# Return recording video webm
						import glob						
						video_files = glob.glob('/tmp/*.webm')
						if video_files:
							recording_video_path = video_files[0] #pick the first one
							st.write('recording_video_path: ', recording_video_path)
							#st.video(recording_video_path)

						HAR_files = glob.glob('/tmp/*.har')
						if HAR_files:
							har_file_path = HAR_files[0] #pick the first one
							st.write(har_file_path)

					except Exception as e:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  

				task = """
				Open https://github.com/browser-use/browser-use
				1. Locate the repository header
				2. Extract:
				- star count
				- fork count
				3. Return result in JSON only:
				{
				"stars": "...",
				"forks": "..."
				}					
				Stop immediately after extraction.
				"""
				asyncio.run(browser_use_func(task))

				st.write(heoquay) 


			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				#st.write(exc_type, fname, exc_tb.tb_lineno)
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  


if __name__ == "__main__":
	myrun()