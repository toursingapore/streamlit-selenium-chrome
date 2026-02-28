import streamlit as st
from bs4 import BeautifulSoup
import time, os, sys, subprocess
from pyngrok import ngrok
import html2text
import requests
from typing import Any, Dict, List, Optional, Type, Union, Callable
from concurrent.futures import ThreadPoolExecutor


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

# ========== START CỤM PCLOUD ==========
from pcloud import PyCloud
#PCLOUD_FOLDER_PATH = "/Temp-video"
# ---------- AUTHENTICATION ----------
def get_pcloud_client(email: str, password: str) -> PyCloud:
	try:
		pc = PyCloud(email, password)
		#st.write(pc) #show all token and methods
		st.success("Connected to pCloud successfully!")
		auth_token = pc.auth_token
		return pc, auth_token
	except Exception as e:
		st.error(f"Authentication failed: {e}")
		raise

# ---------- CREATE FOLDER ----------
def create_folder_pcloud(pc: PyCloud, folder_path: str) -> dict:
	try:
		res = pc.createfolder(path=folder_path)
		if res.get("result") == 0:
			st.info(f"Folder ready: {folder_path}")
		else:
			st.warning(f"Folder creation: {res}")
		return res
	except Exception as e:
		st.error(f"Error creating folder: {e}")
		return {}

# ---------- LISTING ALL FILES IN FOLDER ----------
def list_files_pcloud(pc: PyCloud, folderid: str):
	try:
		#json_data = pc.listfolder(path='/Temp-video')
		#json_data = pc.listfolder(folderid='27763883733')
		json_data = pc.listfolder(folderid=folderid)
		contents = json_data.get("metadata", {}).get("contents", [])
		if not contents:
			st.warning("No files found in folder.")
		else:
			st.success(f"Found {len(contents)} file(s) in {folderid}")
		return contents
	except Exception as e:
		st.error(f"Error listing files: {e}")
		return []

# ---------- DOWNLOAD ALL FILES IN A FOLDER ----------
def download_all_files_in_folder_pcloud(emailpcloud, passpcloud, folderidpcloud):
	pc, auth_token = get_pcloud_client(emailpcloud,passpcloud)
	#List all files in folder 
	result_json_data = list_files_pcloud(pc, folderidpcloud)
	#st.write(result_json_data) 
	video_path_arr = []
	for value in result_json_data:
		fileid = value["fileid"]
		fileName = value["name"]
		created = value["created"]
		st.write(f'fileid: {fileid} - fileName: {fileName} - created: {created}') 

		#Download fileid
		getlink_url = "https://api.pcloud.com/getfilelink"
		params = {
			"fileid": fileid,
			"auth": auth_token,
			'forcedownload': '1',
		}
		response = requests.get(getlink_url, params=params)
		host = response.json()["hosts"][0]
		path = response.json()["path"]
		direct_link_download = f'https://{host}{path}'
		#st.write(direct_link_download)
		response = requests.get(direct_link_download, params=params)
		file_bytes = response.content
		#st.video(file_bytes)
		filename_path = f'/tmp/{fileName}'
		with open(filename_path, 'wb') as f:
			f.write(file_bytes)
		video_path_arr.append(filename_path)
	return video_path_arr 

# ---------- FILE DOWNLOAD ----------
def download_file_pcloud(fileid: str, auth_token: str) -> bytes:
	try:
		res = requests.get(
			"https://api.pcloud.com/getfilelink",
			params={"fileid": fileid, "auth": auth_token, "forcedownload": "1"},
			timeout=10,
		)
		res.raise_for_status()
		data = res.json()
		host, path = data["hosts"][0], data["path"]
		direct_url = f"https://{host}{path}"
		file_response = requests.get(direct_url, timeout=15)
		file_response.raise_for_status()
		return file_response.content
	except Exception as e:
		st.error(f"Failed to download fileid {fileid}: {e}")
		return b""

# ---------- FILE UPLOAD ----------
def upload_files_pcloud(pc: PyCloud, files_Arr: list[str], folder_path: str):
	try:
		result = pc.uploadfile(files=files_Arr, path=folder_path)
		if result.get("result") == 0:
			st.success(f"Uploaded {len(files_Arr)} file(s) to {folder_path}")
		else:
			st.warning(f"Upload response: {result}")
		return result
	except Exception as e:
		st.error(f"Upload failed: {e}")
		return {}
# ========== END CỤM PCLOUD ==========




def myrun():
	st.set_page_config(
		page_title="Web scraping on Streamlit Cloud", 
		page_icon=":star:",
	)     

	with st.sidebar:
		#Navigate to element in current page
		st.markdown(f"<a href='#web-scraper'>WEB SCRAPER</a>", unsafe_allow_html=True)                    
		st.markdown(f"<a href='#connect-postgressql'>CONNECT POSTGRESSQL</a>", unsafe_allow_html=True)
		st.markdown(f"<a href='#colab-test-code'>COLAB TEST CODE</a>", unsafe_allow_html=True)

	st.markdown(
	"""
	## Web scraping on Streamlit Cloud
	[![Source](https://img.shields.io/badge/View-Source-<COLOR>.svg)](https://github.com/snehankekre/streamlit-selenium-chrome/)
	This is a minimal, reproducible example of how to scrape the web with Selenium and Chrome on Streamlit's Community Cloud.
	Fork this repo, and edit `/streamlit_app.py` to customize this app to your heart's desire. :heart:
	"""
	)

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

				execution = desktop.commands.run('python3 -c "print(3 + 5)"')
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
			#print(f"Requesting: {{request.url}}")
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
			#print(screenshot_file)

		except Exception as e:
			print(f"Error during execution: {{e}}")
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

				from prefect import task, flow

				@task(log_prints=False)
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
					result = task_1(param)

					param = result
					task_2(param)

				my_flow()

			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				#st.write(exc_type, fname, exc_tb.tb_lineno)
				st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")  


if __name__ == "__main__":
	myrun()