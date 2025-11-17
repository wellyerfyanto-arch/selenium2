import os
import time
import random
import logging
from flask import Flask, jsonify, render_template, request
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_manager = None

# Import bot manager setelah Flask app diinisialisasi
from bot_manager import BotManager

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    global bot_manager
    if bot_manager:
        return jsonify(bot_manager.get_stats())
    return jsonify({'status': 'Stopped', 'active_tabs': 0})

@app.route('/api/control/start', methods=['POST'])
def control_bot_start():
    global bot_manager
    if not bot_manager:
        bot_manager = BotManager()
    
    data = request.json
    config = data.get('config', {})
    target_urls = data.get('target_urls', [])
    seo_keywords = data.get('seo_keywords', [])
    
    bot_manager.update_config(config)
    
    if not target_urls:
        return jsonify({'status': 'error', 'message': 'No target URLs specified'})
    
    if bot_manager.start_bot(target_urls, seo_keywords):
        return jsonify({
            'status': 'Bot started successfully', 
            'config': bot_manager.config,
            'target_urls': target_urls,
            'seo_keywords': seo_keywords
        })
    else:
        return jsonify({'status': 'Failed to start bot'})

@app.route('/api/control/stop')
def control_bot_stop():
    global bot_manager
    if bot_manager:
        bot_manager.stop_bot()
        return jsonify({'status': 'Bot stopped successfully'})
    return jsonify({'status': 'Bot not running'})

@app.route('/api/config/update', methods=['POST'])
def update_config():
    global bot_manager
    if not bot_manager:
        bot_manager = BotManager()
    
    new_config = request.json.get('config', {})
    bot_manager.update_config(new_config)
    
    return jsonify({
        'status': 'Config updated', 
        'config': bot_manager.config
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)