# 🔬 Q-P Plot Digitizer

A data mining tool for extracting rock mechanics data from published research papers and open access theses. This tool digitizes Q-P (differential stress vs. mean stress) plots to create statistically significant datasets for rock failure strength analysis.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/database-SQLite-green.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Project Overview

This innovative project tests the hypothesis that **rock failure strength can be predicted using only grain size and porosity values** - based on the equivalence of critical state soil mechanics and Byerlee friction (Rutter & Glover, 2012). 

### Key Benefits
- **Faster Analysis**: Avoid expensive and time-consuming laboratory rock mechanics tests
- **Accessible Data**: Extract parameters from borehole wireline logs or visual core analysis
- **Energy Transition**: Accelerate geomechanical assessments for reservoirs, aquifers, and storage sites
- **Public Good**: Enable more rapid decarbonization towards net zero

## 🏛️ Research Collaboration

This project links collaborators from:
- **School of Earth & Environment** 
- **Leeds Institute for Data Analytics (LIDA)**
- **British Geological Survey (BGS)**

## ✨ Features

### 🔬 Plot Digitization
- Upload Q-P plot images (PNG, JPG, JPEG)
- Interactive axis calibration with visual feedback
- Per-sandstone data extraction and validation
- Real-time point visualization with customizable colors

### 📊 Data Management
- SQLite database with comprehensive schema
- Browse and search digitized plots
- Export data as CSV files
- Bulk data operations

### 🔍 Advanced Querying
- **SQL Interface**: Direct database queries with safety controls
- **Natural Language Queries**: AI-powered query generation
- Query history and examples
- Read-only access with automatic limits

### 📈 Analytics & Validation
- Statistical summaries and quality checks
- Plot recreation from digitized data
- Validation overlays and progress tracking
- Database schema visualization

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/qp-plot-digitizer.git
   cd qp-plot-digitizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Access the tool**
   - Open your browser to `http://localhost:8501`
   - Start digitizing Q-P plots!

## 💻 Usage

### 1. Digitize a Plot
1. **Upload**: Select a Q-P plot image
2. **Configure**: Enter DOI, figure number, and number of sandstone datasets
3. **Calibrate**: Click on known axis points to set coordinate system
4. **Extract**: Click on data points for each sandstone individually
5. **Validate**: Review extracted points with visual overlay
6. **Save**: Automatic database storage after validation

### 2. Manage Data
- Browse all digitized plots with search and filtering
- View detailed statistics and data points
- Export individual plots or bulk data as CSV
- Delete plots with cascade removal

### 3. Query Database
- **SQL Tab**: Write custom SQL queries with built-in examples
- **AI Tab**: Ask questions in natural language (requires API token)
- View results in formatted tables
- Export query results as CSV

## 🛠️ Configuration

### Optional: Natural Language Queries
To use AI-powered natural language queries, add your Hugging Face token:

1. **Create `.streamlit/secrets.toml`**:
   ```toml
   HF_TOKEN = "your_hugging_face_token_here"
   ```

2. **Or set environment variable**:
   ```bash
   export HF_TOKEN="your_hugging_face_token_here"
   ```

**Note**: Natural language queries are optional. All core functionality works without API tokens.

## 📁 Project Structure

```
qp-plot-digitizer/
├── app.py                          # Main Streamlit application
├── navigation.py                   # Custom navigation component
├── requirements.txt                # Python dependencies
├── data/                          # SQLite database storage
│   └── plots.db                   # Main database file
├── uploads/                       # Uploaded plot images
├── core/                          # Core functionality modules
│   ├── database.py                # Database management
│   ├── calibrate_axes_streamlit.py # Axis calibration
│   ├── extract_points_streamlit.py # Point extraction
│   ├── streamlit_drawing.py       # Interactive drawing tools
│   ├── recreate_plot.py           # Plot recreation and validation
│   └── query_functions.py         # SQL and NL query handling
└── pages/                         # Streamlit pages
    ├── 1_Plot_Digitisation.py     # Main digitization interface
    ├── 2_Data_Management.py       # Data browsing and management
    ├── 3_DB_Query.py              # Database query interface
    └── 4_Database_Schema.py       # Schema visualization
```

## 🗄️ Database Schema

The tool uses a normalized SQLite database:

- **`plots`**: Publication metadata (DOI, figure number, axis ranges)
- **`sandstones`**: Sandstone dataset information
- **`data_points`**: Individual digitized points (pixel coordinates + converted values)

## 📚 Supported Input Formats

- **Images**: PNG, JPG, JPEG
- **Quality**: Any resolution (higher resolution recommended for accuracy)
- **Content**: Q-P plots with clearly visible axes and data points

## 🔬 Scientific Background

### The Rutter-Glover Hypothesis
The tool tests the hypothesis that rock strength correlates with the product of grain size and porosity, based on the functional equivalence of:
- Critical state soil mechanics
- Byerlee friction law

### Applications
- **Energy Transition**: Geomechanical assessments for renewable energy storage
- **Reservoir Engineering**: Rock strength prediction for oil/gas operations  
- **Carbon Storage**: Site characterization for CO₂ sequestration
- **Geothermal**: Rock mechanics for enhanced geothermal systems

## 🤝 Contributing

We welcome contributions from the research community!

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/qp-plot-digitizer.git

# Install in development mode
pip install -e .

# Run tests (if available)
python -m pytest
```

## 📖 Citation

If you use this tool in your research, please cite:

```bibtex
@software{qp_digitizer_2024,
  title={Q-P Plot Digitizer: A Tool for Rock Mechanics Data Extraction},
  author={[Your Name] and [Collaborators]},
  year={2024},
  url={https://github.com/yourusername/qp-plot-digitizer},
  note={School of Earth \& Environment, LIDA, British Geological Survey}
}
```

**Reference**: Rutter, E.H. and Glover, P.W.J. (2012). The deformation of porous sandstones; are Byerlee friction and the critical state line equivalent? *Journal of Structural Geology*, 44, 129-140.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/yourusername/qp-plot-digitizer/issues)
- **Discussions**: Join community discussions in [GitHub Discussions](https://github.com/yourusername/qp-plot-digitizer/discussions)
- **Documentation**: Check the in-app help and tooltips

### Common Issues
- **Database Connection**: Ensure write permissions in the project directory
- **Image Upload**: Check file format (PNG, JPG, JPEG only)
- **Calibration**: Select points far enough apart for accurate axis scaling
- **Natural Language Queries**: Requires HF_TOKEN for AI functionality

## 🚧 Roadmap

### Planned Features
- **Batch Processing**: Process multiple plots simultaneously
- **Advanced Analytics**: Statistical analysis and visualization tools
- **Export Formats**: Support for additional data formats
- **API Integration**: RESTful API for programmatic access
- **Mobile Support**: Responsive design for tablet digitization

### Known Limitations
- Single plot processing (batch mode planned)
- Manual axis calibration required
- Natural language queries require API token

## 🙏 Acknowledgments

- **School of Earth & Environment** for research guidance
- **Leeds Institute for Data Analytics (LIDA)** for data science expertise  
- **British Geological Survey (BGS)** for domain knowledge
- **Streamlit Community** for the excellent framework
- **Rock Mechanics Research Community** for inspiration and validation

---

**Made with ❤️ for the Energy Transition and Rock Mechanics Research Community**

*Enabling rapid decarbonization through accessible geomechanical data analysis*