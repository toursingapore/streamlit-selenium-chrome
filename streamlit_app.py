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

    website = st.text_input("Enter your website to crawl", value='https://example.com/')
    button = st.button("SUBMIT", type="primary" , key="1")
    if button:
        #Case1; Dùng Linux VM via e2b_desktop và có tích hợp sẵn NoVNC
        from e2b_desktop import Sandbox

        E2B_API_KEY = st.secrets["E2B_API_KEY"]

        # Create with custom resolution and timeout
        desktop = Sandbox.create(api_key=E2B_API_KEY, resolution=(1920, 1080), timeout=600, metadata={"project": "ai-agent-demo"})
        st.write(desktop)

        desktop.launch('google-chrome')  # Alternatives: 'vscode', 'firefox', 'google-chrome', etc.
        desktop.wait(10000)  # Pause to allow the app to initialize (in milliseconds)

        #desktop.open("file.txt")  # Opens default text editor
        #desktop.open("https://google.com")  # Opens default firefox and go to url
        desktop.open(website)
        desktop.wait(10000)

        desktop.write("Hello, world!")
        desktop.press("enter")

        # Save the screenshot to a file
        image = desktop.screenshot()
        screenshot_file = "/tmp/screenshot.png"
        with open(screenshot_file, "wb") as f:
            f.write(image)
        st.image(screenshot_file)

        execution = desktop.files.write("/home/user/example.txt", "Sample content")
        st.write(execution)

        # Start the stream Linux VM via NOVNC
        desktop.stream.start()
        # Get stream URL and able user interaction
        stream_url = desktop.stream.get_url()
        st.write(stream_url)
        # Get stream URL and disable user interaction
        stream_url = desktop.stream.get_url(view_only=True)
        st.write(stream_url)
        # Stop the stream Linux VM via NOVNC
        #desktop.stream.stop()


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

if __name__ == "__main__":
    myrun()