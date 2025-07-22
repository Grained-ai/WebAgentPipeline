# Scripts Directory Organization

This directory has been organized into logical subdirectories for better maintainability and clarity.

## Directory Structure

### 📁 `adhoc/`
Experimental and temporary scripts for ad-hoc tasks:
- `ad_hoc.py` - General purpose ad-hoc script
- `playground.py` - Testing and experimental code

### 📁 `analysis_results/`
Analysis scripts and their documentation:
- `fuzzy_match_checker.py` - Main fuzzy matching script
- `generate_readable_results.py` - Convert results to readable format
- `README_模糊匹配分析.md` - Fuzzy matching analysis documentation

### 📁 `data_files/`
Excel files and data outputs:
- `QC_WebAgent_交付表_20250714_交付表.xlsx` - Delivery table
- `QC_WebAgent_缺漏检查_待确认.xlsx` - Missing items check
- `extracted_instructions.xlsx` - Extracted instructions
- `final_deliver_20250714.xlsx` - Final delivery data
- `steps_without_bbox*.xlsx` - Steps without bounding box data
- `模糊匹配结果.xlsx` - Fuzzy matching results

### 📁 `data_processing/`
Scripts for data transformation and processing:
- `apply_modification.py` - Apply modifications to data
- `combine_*.py` - Various data combination scripts
- `extract_*.py` - Data extraction scripts
- `filter_*.py` - Data filtering scripts
- `json_2_excel.py` - JSON to Excel conversion
- `merge_json_results.py` - Merge JSON results
- `postprocess_*.py` - Post-processing scripts
- `process_*.py` - General processing scripts

### 📁 `quality_control/`
Quality control and validation scripts:
- `calculate_*.py` - Various calculation scripts
- `check_*.py` - Validation and checking scripts
- `generate_qc_excel.py` - Generate QC Excel files
- `register_submited_records.py` - Register submitted records
- `validate_*.py` - Validation scripts

### 📁 `utilities/`
Utility and helper scripts:
- `count_steps.py` - Count steps in data
- `determine_todo_type.py` - Determine task types
- `final_deliver.py` - Final delivery operations
- `move_image.py` - Image file operations
- `re-generate_screenshots.py` - Screenshot regeneration
- `remove_end_image.py` - Remove end images
- `select_all_wo_delete.py` - Selection operations
- `sub_step_type.py` - Sub-step type operations
- `summarize_jsons_version.py` - JSON version summarization
- `test_selenium_crop.py` - Selenium testing

## Usage Guidelines

1. **adhoc/**: Use for temporary experiments and one-off scripts
2. **analysis_results/**: Place analysis scripts and their documentation here
3. **data_files/**: Store all Excel/CSV data files here
4. **data_processing/**: Scripts that transform or process data
5. **quality_control/**: QC, validation, and checking scripts
6. **utilities/**: Reusable helper scripts and utilities

## Maintenance

- Keep scripts in their appropriate directories
- Update this README when adding new categories
- Consider moving frequently used adhoc scripts to appropriate permanent directories