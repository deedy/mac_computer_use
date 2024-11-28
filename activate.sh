#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "Virtual environment activated!"
echo ""
echo "To start the application:"
echo "1. Set your API key:"
echo "   export ANTHROPIC_API_KEY=your_api_key_here"
echo "2. Set display dimensions (recommended):"
echo "   export WIDTH=1280"
echo "   export HEIGHT=800"
echo "3. Run the Streamlit app:"
echo "   streamlit run streamlit.py"
