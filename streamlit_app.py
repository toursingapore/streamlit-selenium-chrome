import streamlit as st
from bs4 import BeautifulSoup
import time, os, sys, subprocess
from pyngrok import ngrok
import html2text
import requests
from typing import Any, Dict, List, Optional, Type, Union, Callable
from concurrent.futures import ThreadPoolExecutor
import os
import base64
from base64 import b64encode
import asyncio
import nest_asyncio
nest_asyncio.apply() #Enable asyncio in the main thread and Run the asynchronous function

from prefect import task, flow
from prefect.schedules import Cron


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
		GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
		
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
		st.markdown(f"<a href='#discord-bot'>DISCORD BOT</a>", unsafe_allow_html=True)
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
		st.write("## WEB SCRAPER")

		website = st.text_input("Enter your website to crawl", value="https://www.browserscan.net/bot-detection")
		button = st.button("SUBMIT", type="primary" , key="1")
		if button:
			try:
				#Case1; Dùng Linux VM via e2b_desktop và có tích hợp sẵn NoVNC
				import e2b_desktop
				with st.expander("Click here to view data - e2b_desktop"):
					st.write('e2b_desktop',e2b_desktop)    
							
				from e2b_desktop import Sandbox, AsyncSandbox, Template
				with st.expander("Click here to view data - AsyncSandbox"):
					st.write('AsyncSandbox',AsyncSandbox)

				E2B_API_KEY = st.secrets["E2B_API_KEY"]

				desktop = Sandbox.create(
					api_key=E2B_API_KEY,
					resolution=(1366, 768),
					timeout=3600, #max live 1hour
					metadata={"project": "ai-agent-demo"},
				)
				desktop.wait(3000)
				#execution = desktop.commands.run("echo $E2B_TEMPLATE_ID")
				#st.write('E2B_TEMPLATE_ID: ',execution.stdout)                        

				execution = desktop.commands.run("lsb_release -a")
				st.write('Running OS: ',execution.stdout)

				execution = desktop.commands.run('python3 -c "st.write(3 + 5)"')
				st.write("Python Output:", execution.stdout)

				#Stream toàn bộ Linux VM
				# Start the stream Linux VM via NOVNC
				desktop.stream.start()
				# Get stream URL and able user interaction (vào link này tương tác trực tiếp với Linux VM)
				stream_url = desktop.stream.get_url()
				st.write(stream_url)
				# Get stream URL and disable user interaction
				stream_url = desktop.stream.get_url(view_only=True)
				st.write(stream_url)
				# Stop the stream Linux VM via NOVNC - mỗi lần chỉ stream được 1 app only
				#desktop.stream.stop()

				# Pause the app to initialize (milliseconds), then Save the screenshot to a file
				desktop.wait(10000)  
				image = desktop.screenshot()
				screenshot_file = "/tmp/screenshot.png"
				with open(screenshot_file, "wb") as f:
					f.write(image)
				st.image(screenshot_file)

				#Sau khi VM init xong thì cài python and system packages
				execution = desktop.commands.run("pip install --user requests patchright==1.55.2 html2text==2025.4.15 nest_asyncio")
				#st.write(execution.stdout)
				execution = desktop.commands.run("sudo apt install curl ffmpeg -y")
				#st.write(execution.stdout)

				#Check ip
				execution = desktop.commands.run('curl http://ifconfig.me/')
				st.write("Info IP:", execution.stdout)

				#desktop.launch('google-chrome')  # mở ứng dụng - Alternatives: 'vscode', 'firefox', 'google-chrome', etc.
				#desktop.wait(10000)  # Pause to allow the app to initialize (in milliseconds)

				python_script = f"""
import asyncio
import nest_asyncio
nest_asyncio.apply()
from patchright.async_api import async_playwright

async def myfunc(display_intercept=False):
	async with async_playwright() as p:
		browser = None
		
		# Define logging function for all requests
		async def log_and_continue_request(route, request):
			#st.write(f"Requesting: {{request.url}}")
			await route.continue_() 

		try:
			browser = await p.chromium.launch_persistent_context(
				user_data_dir="/tmp/profile",
				headless=False,
				channel="chrome",
				executable_path="/usr/bin/google-chrome",  # nếu cần dùng chrome cụ thể
				viewport={{"width": 1366, "height": 768}},
				user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.165 Safari/537.36", #User-agent phù hợp current Google Chrome 134.0.6998.165 mới chuẩn được
				args=[
					"--disable-blink-features=AutomationControlled",
					"--no-sandbox",
					"--disable-dev-shm-usage",
					"--disable-infobars"  # không luôn có hiệu lực nhưng thử thêm
				],
				# Loại bỏ default arg --enable-automation vốn sinh ra infobar
				ignore_default_args=["--enable-automation"],
			)

			# Access the first page or create a new one
			pages = browser.pages
			page = pages[0] if pages else await browser.new_page()

			# Set context-level settings AFTER launch
			await page.context.grant_permissions(["geolocation"])
			await page.context.set_geolocation({{"longitude": 12.492507, "latitude": 41.889938}})
			await page.context.set_extra_http_headers({{"Accept-Language": "en-US"}})

			if display_intercept:
				#Intercept with async handler
				await page.route("**/*", log_and_continue_request)

			await page.goto("https://www.google.com/search?q=gi%C3%A1+v%C3%A0ng", wait_until='load')             
			await page.wait_for_timeout(10000)

			#Phải vào google trước để lấy cookies, nếu vào thẳng luôn sẽ bị 'Sign in to confirm you're not a bot'
			await page.goto("{website}", referer="https://www.google.com/", wait_until='load')            
			await page.wait_for_timeout(10000)                 

			# Dùng code cho youtube auto play
			await page.evaluate("document.querySelector('video').muted = true")
			await page.evaluate("document.querySelector('video').play()")
			await asyncio.sleep(3600)

			#screenshot_file = "/tmp/example.png"
			#await page.screenshot(path=screenshot_file)
			
			#await asyncio.sleep(120)
			#st.write(screenshot_file)

		except Exception as e:
			st.write(f"Error during execution: {{e}}")
		finally:
			if browser:
				#await browser.close()
				pass

asyncio.run(myfunc(display_intercept=True))
#await myfunc(display_intercept=True) #Use this when running in colab mới work            
				"""

				# Write python script file
				execution = desktop.files.write("/tmp/file.py", python_script)
				st.write(execution)            
				# Run python script file with timeout=0 is wait until code finished (default process timeout 30 seconds)
				execution = desktop.commands.run("python3 /tmp/file.py", background=False, timeout=0) 
				st.write(execution.stdout)

				_ = """
				# Open a file
				desktop.open("/tmp/example.png")

				# Pause the app to initialize (milliseconds), then Save the screenshot to a file
				desktop.wait(10000)  
				image = desktop.screenshot()
				screenshot_file = "/tmp/screenshot.png"
				with open(screenshot_file, "wb") as f:
					f.write(image)
				st.image(screenshot_file)

				# Get current (active) window ID
				window_id = desktop.get_current_window_id()
				# Get window title
				title = desktop.get_window_title(window_id)     
				st.write('Title of current active window id: ',title)

				# Get all windows of the application
				window_ids = desktop.get_application_windows("Firefox")
				st.write(window_ids)

				desktop.write("Hello, world!")
				desktop.press("enter")

				execution = desktop.files.write("/home/user/example.txt", "Sample content")
				st.write(execution)

				#stream window_id only
				window_id = desktop.get_current_window_id() #get active window id
				st.write('window_id - ',window_id)
				desktop.stream.start(
					window_id=window_id, # if not provided the whole desktop will be streamed
					require_auth=False
				)
				stream_url = desktop.stream.get_url()
				st.write(stream_url)
				# Stop the stream window_id - mỗi lần chỉ stream được 1 app only
				#desktop.stream.stop()        
				_ = """


				_ = """
				#Case2; Tự code Linux VM tích hợp NoVNC in streamlit cloud
				#run_command_line("wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip -P /tmp")
				#run_command_line("unzip /tmp/ngrok-stable-linux-amd64.zip -d /tmp/ngrok-stable-linux-amd64")
				#run_command_line("ls -a /tmp/ngrok-stable-linux-amd64")   
				#ngrok_authtoken = '2elQfBKwd0CX0jFToGi7zZVRoAI_2muVgZUZ2agRUxWCoCrqF'
				#run_command_line(f"/tmp/ngrok-stable-linux-amd64/ngrok authtoken {ngrok_authtoken}")
				#run_command_line("/tmp/ngrok-stable-linux-amd64/ngrok http 3000")

				if not os.path.isdir('/tmp/noVNC'):    
					run_command_line("git clone https://github.com/novnc/noVNC.git /tmp/noVNC")  
					run_command_line("ls -la /tmp/noVNC/utils")
					run_command_line("chmod +x /tmp/noVNC/utils/novnc_proxy")       
					run_command_line("/tmp/noVNC/utils/novnc_proxy --vnc localhost:5901 --listen 3000 &") #run cmd in background with '&' 
				st.write('forward internal port 5901 of VNC to 3000 - DONE')
				
				try:
					NGROK_AUTHTOKEN = '2elQfBKwd0CX0jFToGi7zZVRoAI_2muVgZUZ2agRUxWCoCrqF'
					ngrok.set_auth_token(NGROK_AUTHTOKEN)
					ngrok_tunnel = ngrok.connect("3000")
					st.write(ngrok_tunnel, ngrok_tunnel.public_url)        

				except Exception as e:
					ngrok.kill() #kill all running tunnel in advance        
					exc_type, exc_obj, exc_tb = sys.exc_info()
					fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
					#st.write(exc_type, fname, exc_tb.tb_lineno)
					st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}") 

				#run_command_line("whereis novnc && whereis vncserver") 
				#run_command_line('echo "nicepassword" | vncpasswd -f > ~/.vnc/passwd')     
				#run_command_line("chmod 600 ~/.vnc/passwd")           
				#run_command_line("vncserver :1")       
				#run_command_line("websockify -D --web=/usr/share/novnc/ 3000 localhost:5901")        

				st.write(f"your website is {website}")  
				with st.container():
					with st.spinner('Wait for it...'):
						time.sleep(5)

						#@st.cache_resource  #Phải chuyển comment cái này để nó ko nhớ cache và crawl nhiều urls được
						def get_driver():
							return webdriver.Chrome(
								service=Service(
									ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
								),
								options=options,
							)

						options = Options()
						options.add_argument("--disable-gpu")
						options.add_argument("--headless=new")
						options.add_argument('--no-sandbox')
						options.add_argument('--disable-dev-shm-usage')
						options.add_argument("--enable-javascript")
						options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G988B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/20.0 Chrome/106.0.5249.126 Mobile Safari/537.36")
						#proxy = '23.23.23.23:3128'
						#options.add_argument('--proxy-server='+proxy) #use proxy with --proxy-server=23.23.23.23:3128
						#options.add_argument('--proxy-server=socks5://'+proxy) #use socks5 with --proxy-server=socks5://23.23.23.23:3128

						driver = get_driver()
						driver.get(website) #driver.get("https://vnexpress.net")

						def wait_for_page_load(driver): 
							return driver.execute_script('return document.readyState') == 'complete'             
						
						Page_Loaded = wait_for_page_load(driver)
						if Page_Loaded:
							st.write(f"Page Loaded: {Page_Loaded}")

							html = driver.page_source
							#st.code(html) #show code html để user nhìn thấy
							st.markdown(html, unsafe_allow_html=True) #load html and render it in streamlit page
							
							#Đưa vào BeautifulSoup cho dễ scrape elements
							soup = BeautifulSoup(html)
							for tag in soup.find_all('title'):
								st.write(tag.text)
							for tag_body in soup.find_all('body'):
								st.write(tag_body.text)

							time.sleep(5000)

							# Quit the driver
							driver.close()
							driver.quit()
					st.success('Done!')
				_ = """
			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")   

	with st.container(border=True):   
		st.write("## DISCORD BOT")

		button = st.button("SUBMIT", type="primary" , key="24dfdasb235")
		if button:
			try:
				st.write("Started Discord Bot in background.")

				DISCORD_TOKEN = st.secrets["DISCORD_TOKEN"]

				import discord
				from discord.ext import commands

				# Khởi tạo client bot với intents
				intents = discord.Intents.default()
				intents.typing = False # False: bot sẽ bỏ sự kiện khi user đang gõ tin nhắn (on_typing)
				intents.presences = False # Ignore check trạng thái bot
				intents.message_content = True # Cho phép bot đọc nội dung tin nhắn. Bạn phải bật trong Discord Developer Portal: Bot → Privileged Gateway Intents → bật "Message Content Intent"
				bot = commands.Bot(command_prefix="!", intents=intents)

				@bot.event
				async def on_ready():
					print(f"Bot đã đăng nhập: {bot.user}")								

				@bot.event
				async def on_message(message):
					if message.author == bot.user:
						return

					# BỎ QUA nếu là command (bắt đầu bằng prefix '!')
					if message.content.startswith(bot.command_prefix):
						await bot.process_commands(message)
						return

					# ===== XỬ LÝ ẢNH =====
					if message.attachments:
						for attachment in message.attachments:
							# Kiểm tra file có phải ảnh không
							if attachment.content_type and attachment.content_type.startswith("image"):
								# Option 1: lấy URL ảnh
								#image_url = attachment.url

								# Option 2: tải file về RAM
								image_bytes = await attachment.read()
								image_path = "/tmp/image.png"
								with open(image_path, "wb") as f:
									f.write(image_bytes)

								prompt = message.content
								reply = chatbot_vision_by_groq(prompt, image_path=image_path)

								reply = image_path + ' - ' + reply
								await message.channel.send(str(reply))
								return

					# ===== XỬ LÝ TEXT =====
					if message.content:
						try:
							prompt = message.content
							reply = chatbot_vision_by_groq(prompt)
							await message.channel.send(str(reply))
						except Exception as e:
							exc_type, exc_obj, exc_tb = sys.exc_info()
							fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
							reply = f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}" 
							await message.channel.send(str(reply))
					await bot.process_commands(message)							

				@bot.command()
				#Định nghĩa command theo function name là help và prefix là '!', thì client PHẢI gõ '!helpme'
				async def helpme(ctx):
					reply = """List commands:
!clear 100 (remove 100 latest messages)
!shutdown (exit bot)
					"""
					await ctx.send(str(reply))

				@bot.command()
				@bot.describe(myArr='Please select one.')
				@bot.choices(myArr=[
					Choice(name='apple', value=1),
					Choice(name='banana', value=2),
					Choice(name='cherry', value=3),
				])
				async def fruit(interaction: discord.Interaction, myArr: Choice[int]):
					reply = f'Your favourite fruit is {myArr.name}.'
					await interaction.response.send_message(str(reply))

				@bot.command()
				@commands.has_permissions(manage_messages=True)
				async def clear(ctx, amount: int = 10): # !clear 100 -> xóa 100 tin nhắn gần nhất 
					try:
						if amount <= 0:
							await ctx.send("Số lượng phải > 0")
							return
						# Giới hạn Discord: tối đa 100/lần
						amount = min(amount, 100)
						deleted = await ctx.channel.purge(limit=amount + 1)  # +1 để xóa luôn lệnh !clear
						msg = await ctx.send(f"Đã xóa {len(deleted)-1} tin nhắn")
						await asyncio.sleep(3)
						await msg.delete()
					except Exception as e:
						await ctx.send(f"Error: {e}")

				@bot.command()
				@commands.is_owner()
				async def shutdown(ctx): # !shutdown -> wait 3 min to turn off bot và stop in background đây luôn
					await ctx.send('Shutting down...It takes about 3 minutes')
					await bot.close()

				# Chạy bot với token của bạn
				bot.run(DISCORD_TOKEN)

			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")   

	with st.container(border=True):   
		st.write("## PYTHON WORKFLOW PIPELINES")

		button = st.button("SUBMIT", type="primary" , key="24dfdas5vb235")
		if button:
			try:
				st.write('Hello world')

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
				st.write('Hello world') 

				import openvpn_api.VPN
				v = openvpn_api.VPN('localhost', 7505)
				v.connect()
				# Do some stuff, e.g.
				st.write(v.release)
				v.disconnect()

			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				#st.write(exc_type, fname, exc_tb.tb_lineno)
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  


if __name__ == "__main__":
	myrun()