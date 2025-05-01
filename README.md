# Venus XSS Scanner 🌟

Venus XSS Scanner is a powerful and modern Cross-Site Scripting (XSS) vulnerability scanner with real-time Telegram notifications and advanced WAF bypass capabilities.

## 📖 Description

Venus XSS Scanner is an advanced security tool designed to detect Cross-Site Scripting (XSS) vulnerabilities in web applications. Built with modern Python, it combines high-performance concurrent scanning with sophisticated WAF bypass techniques to provide thorough security assessments.

### Key Highlights:
- 🔍 **Intelligent Scanning**: Automatically detects and tests various injection points including URL parameters, paths, and fragments
- 🛡️ **WAF Bypass**: Implements multiple encoding techniques and evasion strategies to bypass Web Application Firewalls
- 🚀 **High Performance**: Utilizes concurrent processing for faster scanning while maintaining accuracy
- 📱 **Real-time Alerts**: Integrates with Telegram for instant vulnerability notifications
- 🌐 **Multi-Browser Support**: Compatible with Chrome, Firefox, Edge, and Safari for comprehensive testing
- 📊 **Detailed Reporting**: Generates both detailed JSON reports and simple TXT summaries

### Use Cases:
- Security auditing of web applications
- Penetration testing assignments
- Continuous security assessments
- Bug bounty hunting
- Educational purposes and security research

## 🔧 Technical Details

### Architecture
- **Multi-threaded Engine**: Implements ThreadPoolExecutor for parallel scanning
- **Browser Automation**: Uses Selenium WebDriver with multiple browser support
- **Smart Payload Generation**: Automatic encoding and WAF bypass variation generation
- **Real-time Monitoring**: Asynchronous progress tracking and notification system

### Security Features
- **WAF Detection**: Intelligent detection of Web Application Firewalls
- **Evasion Techniques**: Multiple payload encoding methods including:
  - HTML encoding
  - URL encoding
  - Unicode encoding
  - Double encoding
  - Mixed encoding
- **Parameter Analysis**: Smart detection of injectable parameters
- **Context-Aware Testing**: Adapts payloads based on injection context

### Performance Optimization
- **Resource Management**: Smart browser pool management
- **Concurrent Processing**: Efficient handling of multiple test cases
- **Memory Efficient**: Streaming processing of large URL lists
- **Timeout Management**: Adaptive timeout handling for different scenarios

![Venus XSS Scanner](https://img.shields.io/badge/Venus-XSS%20Scanner-ff69b4)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌈 Features

- 🚀 High-performance concurrent scanning
- 🔥 Advanced WAF bypass techniques
- 📱 Real-time Telegram notifications
- 🎨 Beautiful CLI interface with progress tracking
- 🛡️ Multiple browser engine support (Chrome, Firefox, Edge, Safari)
- 📊 Detailed HTML and JSON reports
- 🔄 Automatic payload encoding and variations
- ⚡ Smart parameter detection and injection
- 🌐 Support for various URL components (path, query, fragment)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/venus-xss.git
cd venus-xss
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have at least one of these browsers installed:
- Google Chrome
- Mozilla Firefox
- Microsoft Edge
- Safari

### Chrome and ChromeDriver Installation (Linux)

If you need to install Chrome and ChromeDriver on Linux, follow these steps:

1. Install Google Chrome:
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# If you encounter any errors during installation, run:
sudo apt -f install
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

2. Install ChromeDriver:
```bash
wget https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
cd chromedriver-linux64 
sudo mv chromedriver /usr/bin
```

## 🎮 Usage

Run the scanner:
```bash
python xss_validator.py
```

The interactive menu will guide you through:
1. URL input (single URL or file with URLs)
2. Payload selection (custom file or default payloads)
3. Scan timeout configuration
4. Telegram notification setup (optional)

### 🤖 Telegram Bot Setup

1. Start a chat with @VenusXSS_bot on Telegram
2. Use the `/start` command to get started
3. Use `/id` to get your Chat ID
4. Enter your Chat ID in the scanner when prompted

## 📝 Input Formats

### URLs File Format
```text
https://example.com/page1
https://example.com/page2?param=test
https://example.com/page3#fragment
```

### Custom Payloads File Format
```text
<script>alert(1)</script>
<img src=x onerror=alert(1)>
javascript:alert(1)
```

## 📊 Reports

The scanner generates two types of reports:
1. Detailed JSON report with scan statistics
2. Simple TXT report with vulnerable URLs

Reports are automatically saved with timestamps in the current directory.

## ⚙️ Configuration

The scanner supports various configuration options through the interactive menu:
- Custom timeout values
- Multiple browser engines
- Various payload encoding methods
- WAF bypass techniques

## 🛡️ Disclaimer

This tool is for educational and ethical testing purposes only. Always obtain proper authorization before scanning any website.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🌟 Credits

Developed by Venus Security 