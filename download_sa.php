<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SA Shell - Download</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
            color: white;
        }

        .header h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.3rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }

        .download-section {
            background: white;
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }

        .download-options {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .download-option {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
        }

        .download-option:hover {
            border-color: #667eea;
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
        }

        .download-option h3 {
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .download-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 1rem 0;
        }

        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .terminal-section {
            background: #2d3748;
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .terminal-section h3 {
            color: #e2e8f0;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .terminal-code {
            background: #1a202c;
            border-radius: 10px;
            padding: 1.5rem;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            color: #e2e8f0;
            overflow-x: auto;
            margin: 1rem 0;
        }

        .terminal-code code {
            display: block;
            line-height: 1.8;
        }

        .copy-btn {
            background: #4a5568;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-top: 1rem;
            transition: background 0.3s ease;
        }

        .copy-btn:hover {
            background: #2d3748;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .feature {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .feature h4 {
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }

        .performance-note {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }

        .performance-note h3 {
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }

        .footer {
            text-align: center;
            color: white;
            opacity: 0.8;
            margin-top: 3rem;
        }

        @media (max-width: 768px) {
            .download-options {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2.5rem;
            }
            
            .container {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SA Shell</h1>
            <p>A fast, interactive shell for the SA Query Language. Download and install in seconds.</p>
        </div>

        <div class="download-section">
            <h2 style="text-align: center; margin-bottom: 2rem; color: #667eea; font-size: 2rem;">Download Options</h2>
            
            <div class="download-options">
                <div class="download-option">
                    <h3>🖥️ Desktop Download</h3>
                    <p>Download the installer binary directly to your computer</p>
                    <a href="sa-installer" class="download-btn" download>Download Installer</a>
                    <p style="font-size: 0.9rem; color: #666; margin-top: 1rem;">~11 MB • macOS/Linux</p>
                </div>
                
                <div class="download-option">
                    <h3>📱 Mobile/Tablet</h3>
                    <p>Get the terminal commands to install from your device</p>
                    <a href="#terminal-instructions" class="download-btn">View Commands</a>
                    <p style="font-size: 0.9rem; color: #666; margin-top: 1rem;">Copy & paste commands</p>
                </div>
            </div>
        </div>

        <div class="terminal-section" id="terminal-instructions">
            <h3>💻 Terminal Installation</h3>
            <p style="color: #a0aec0; margin-bottom: 1rem;">Run these commands in your terminal to download and install:</p>
            
            <div class="terminal-code">
                <code># Download the installer</code>
                <code>curl -L -o sa-installer https://zubatomic.com/sa-installer</code>
                <code></code>
                <code># Make it executable</code>
                <code>chmod +x sa-installer</code>
                <code></code>
                <code># Run the installer</code>
                <code>./sa-installer</code>
            </div>
            
            <button class="copy-btn" onclick="copyCommands()">📋 Copy Commands</button>
        </div>

        <div class="performance-note">
            <h3>⚡ Lightning Fast Performance</h3>
            <p><strong>First run:</strong> ~25 seconds (download + install) • <strong>Subsequent runs:</strong> 0.5-1.2 seconds!</p>
        </div>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">🔧</div>
                <h4>Easy Installation</h4>
                <p>One command installation with automatic PATH setup</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">🚀</div>
                <h4>Fast Startup</h4>
                <p>Optimized binary with intelligent caching for speed</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">💻</div>
                <h4>Cross-Platform</h4>
                <p>Works on macOS, Linux, and Windows</p>
            </div>
            
            <div class="feature">
                <div class="feature-icon">📚</div>
                <h4>Interactive Shell</h4>
                <p>Full-featured shell with query language support</p>
            </div>
        </div>

        <div class="footer">
            <p>SA Shell - Powered by the SA Framework</p>
            <p style="margin-top: 0.5rem; font-size: 0.9rem;">Built with PyInstaller • Distributed via zubatomic.com</p>
        </div>
    </div>

    <script>
        function copyCommands() {
            const commands = `# Download the installer
curl -L -o sa-installer https://zubatomic.com/sa-installer

# Make it executable
chmod +x sa-installer

# Run the installer
./sa-installer`;
            
            navigator.clipboard.writeText(commands).then(() => {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                btn.style.background = '#48bb78';
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '#4a5568';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
                alert('Failed to copy commands. Please copy manually.');
            });
        }
    </script>
</body>
</html>
