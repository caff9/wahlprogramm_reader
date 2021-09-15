mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
[theme]\n\
backgroundColor='#FFFFFF'\n\
primaryColor='#22bd0a'\n\
secondaryBackgroundColor='#d2d2d2'\n\
textColor='#000000'\n\
\n\
" > ~/.streamlit/config.toml
