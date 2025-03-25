# gpt_web_scraper
Download the website with a single python script, convert it to markdowns and get a summary of the information you want with chat gpt

1. Architectural Structure
The application is designed with object-oriented programming (OOP) principles and organized around a single class. This class encapsulates web scraping, content transformation and OpenAI API integration functionality.
2. Basic Components
2.1. Web Scraping Module
pulls web page content using requests library
Added user agent and proxy support
Try-except blocks are used for error handling
2.2. HTML-to-Markdown Converter
Parse HTML content with BeautifulSoup4
Unnecessary elements (script, style, iframe, etc.) are cleaned
convert HTML content to Markdown format with markdownify library
Markdown content is cleaned and optimized with regular expressions (regex)
2.3. OpenAI API Integration
New API version of OpenAI (1.0.0+) is used
Client is created with OpenAI class
Content is processed with the Chat Completions API
Responses are structured in JSON format

3. Important Technical Details
3.1. Content Optimization
15,000 character limit applies for long content (for GPT-3.5)
Markdown content is cleaned and unnecessary parts are removed
Code blocks are processed using regular expressions for JSON responses
3.2. Error Management
All critical operations are done within try-except blocks
The logging module is used for detailed logging
API errors are caught and meaningful messages are presented to the user
3.3. Performance Optimization
Unnecessary HTTP requests are avoided
Content size is optimized
API parameters (temperature, top_p, max_tokens) are adjusted for efficiency
4. Data Flow
Web page content is scraped with scrape_with_requests()
HTML content is converted to Markdown with html_to_markdown()
Markdown content is sent to the OpenAI API with process_with_openai()
API response is converted to JSON format
The results are saved in a file and printed on the screen
5. Safety and Durability
API keys are stored directly in the code (in real applications environmental variables should be used)
Connection timeouts and retry mechanisms are added
Protection against IP blocking with proxy support
This app offers a modern approach to web scraping and AI integration and works in line with the latest API version of OpenAI.
