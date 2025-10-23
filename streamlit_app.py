import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import time, os, sys
from pyngrok import ngrok



def run_command_line(command):
    import sys, subprocess
    try:
        # Run the command and capture the output
        output = subprocess.check_output(command, shell=True)
        output = output.decode('utf-8')
        # Split the output into a list of lines
        lines = output.split('\n')
        # Write each line separately
        for line in lines:
            st.write(line)
    except subprocess.CalledProcessError as e:
        st.write(f"An error occurred: {e}")

def myrun():
    st.set_page_config(
        page_title="Web scraping on Streamlit Cloud with Selenium",
        page_icon=":star:",
    )    
    """
    ## Web scraping on Streamlit Cloud with Selenium

    [![Source](https://img.shields.io/badge/View-Source-<COLOR>.svg)](https://github.com/snehankekre/streamlit-selenium-chrome/)

    This is a minimal, reproducible example of how to scrape the web with Selenium and Chrome on Streamlit's Community Cloud.

    Fork this repo, and edit `/streamlit_app.py` to customize this app to your heart's desire. :heart:
    """

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
                viewport={{"width": 1280, "height": 800}},
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

            #await page.goto("https://www.browserscan.net/bot-detection", wait_until='load')
            await page.goto("{website}", wait_until='load')            
            await page.wait_for_timeout(10000)     

            # Dùng code cho youtube auto play
            await page.evaluate("document.querySelector('video').muted = true")
            await page.evaluate("document.querySelector('video').play()")
            await asyncio.sleep(3600)

            screenshot_file = "/tmp/example.png"
            await page.screenshot(path=screenshot_file)
            
            #await asyncio.sleep(120)
            print(screenshot_file)

        except Exception as e:
            print(f"Error during execution: {{e}}")
        finally:
            if browser:
                await browser.close()

asyncio.run(myfunc(display_intercept=True))
#await myfunc(display_intercept=True) #Use this when running in colab mới work            
            """

            # Write python script file
            execution = desktop.files.write("/tmp/file.py", python_script)
            st.write(execution)            
            # Run python script file with timeout=0 is wait until code finished (default process timeout 30 seconds)
            execution = desktop.commands.run("python3 /tmp/file.py", background=False, timeout=0) 
            st.write(execution.stdout)

            # Open a file
            desktop.open("/tmp/example.png")

            # Pause the app to initialize (milliseconds), then Save the screenshot to a file
            desktop.wait(10000)  
            image = desktop.screenshot()
            screenshot_file = "/tmp/screenshot.png"
            with open(screenshot_file, "wb") as f:
                f.write(image)
            st.image(screenshot_file)

            _ = """
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

if __name__ == "__main__":
    myrun()