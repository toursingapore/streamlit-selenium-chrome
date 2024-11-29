import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import time

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


"""
## Web scraping on Streamlit Cloud with Selenium

[![Source](https://img.shields.io/badge/View-Source-<COLOR>.svg)](https://github.com/snehankekre/streamlit-selenium-chrome/)

This is a minimal, reproducible example of how to scrape the web with Selenium and Chrome on Streamlit's Community Cloud.

Fork this repo, and edit `/streamlit_app.py` to customize this app to your heart's desire. :heart:
"""

website = st.text_input("Enter your website to crawl", value='https://example.com/')
button = st.button("SUBMIT", type="primary" , key="1")
if button:
    #run_command_line("git clone https://github.com/novnc/noVNC.git /tmp/noVNC") 
    run_command_line("ls -la /tmp/noVNC/utils")     

    #run_command_line("whereis novnc && whereis vncserver") 
    #run_command_line("ls -la /usr/share/novnc")  
    #run_command_line('echo "nicepassword" | vncpasswd -f > ~/.vnc/passwd')     
    #run_command_line("chmod 600 ~/.vnc/passwd")           
    #run_command_line("vncserver :1")       
    #run_command_line("sudo websockify -D --web=/usr/share/novnc/ 80 localhost:5901")        


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

                # Quit the driver
                #driver.close()
                #driver.quit()
        st.success('Done!')
