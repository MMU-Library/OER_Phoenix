// static/admin/js/oer_source_dynamic.js
document.addEventListener('DOMContentLoaded', function() {
    const sourceTypeSelect = document.getElementById('id_source_type');
    
    function toggleConfigSections() {
        const selectedType = sourceTypeSelect ? sourceTypeSelect.value : '';
        
        console.log('Selected source type:', selectedType);
        
        // Hide all config sections first
        document.querySelectorAll('.api-config, .oaipmh-config, .csv-config, .marcxml-config').forEach(section => {
            section.style.display = 'none';
            section.classList.add('hidden');
        });
        
        // Show the relevant section
        if (selectedType === 'API') {
            document.querySelectorAll('.api-config').forEach(section => {
                section.style.display = 'block';
                section.classList.remove('hidden');
            });
        } else if (selectedType === 'OAIPMH') {
            document.querySelectorAll('.oaipmh-config').forEach(section => {
                section.style.display = 'block';
                section.classList.remove('hidden');
            });
        } else if (selectedType === 'CSV') {
            document.querySelectorAll('.csv-config').forEach(section => {
                section.style.display = 'block';
                section.classList.remove('hidden');
            });
        } else if (selectedType === 'MARCXML') {
            document.querySelectorAll('.marcxml-config').forEach(section => {
                section.style.display = 'block';
                section.classList.remove('hidden');
            });
        }
        
        updateFieldRequirements(selectedType);
        updatePresetButtons(selectedType);
    }
    
    function updateFieldRequirements(sourceType) {
        const apiEndpoint = document.getElementById('id_api_endpoint');
        const oaipmhUrl = document.getElementById('id_oaipmh_url');
        const csvUrl = document.getElementById('id_csv_url');
        const marcxmlUrl = document.getElementById('id_marcxml_url');
        
        // Reset all
        if (apiEndpoint) apiEndpoint.required = false;
        if (oaipmhUrl) oaipmhUrl.required = false;
        if (csvUrl) csvUrl.required = false;
        
        // Set based on source type
        if (sourceType === 'API' && apiEndpoint) {
            apiEndpoint.required = true;
        } else if (sourceType === 'OAIPMH' && oaipmhUrl) {
            oaipmhUrl.required = true;
        } else if (sourceType === 'CSV' && csvUrl) {
            csvUrl.required = true;
        } else if (sourceType === 'MARCXML' && marcxmlUrl) {
            marcxmlUrl.required = true;
        }
    }
    
    // Initial setup
    if (sourceTypeSelect) {
        toggleConfigSections();
        sourceTypeSelect.addEventListener('change', toggleConfigSections);
    }
    
    // Enable/disable preset buttons based on selected source type
    function updatePresetButtons(selectedType) {
        document.querySelectorAll('.preset-button.specific').forEach(btn => {
            const btnType = btn.getAttribute('data-type');
            if (!btnType) return;
            if (selectedType === btnType) {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            } else {
                btn.disabled = true;
                btn.style.opacity = '0.45';
                btn.style.cursor = 'not-allowed';
            }
        });
    }
    
    // Make available globally
    window.toggleConfigSections = toggleConfigSections;
    window.updatePresetButtons = updatePresetButtons;

    // Attach config classes to rendered admin form rows so toggleConfigSections can find them
    function attachFieldRowClass(fieldId, className) {
        try {
            const el = document.getElementById(fieldId);
            if (!el) return;
            // Find nearest form-row (admin default structure)
            let row = el.closest('.form-row');
            if (!row) {
                // fallback to parent element wrappers used by some Django versions
                row = el.parentElement && el.parentElement.parentElement ? el.parentElement.parentElement : el.parentElement;
            }
            if (row) row.classList.add(className);
        } catch (e) {
            console.warn('attachFieldRowClass failed for', fieldId, e);
        }
    }

    // Attach known fields
    ['id_api_endpoint','id_request_headers','id_request_params'].forEach(f => attachFieldRowClass(f, 'api-config'));
    ['id_oaipmh_url','id_oaipmh_set_spec'].forEach(f => attachFieldRowClass(f, 'oaipmh-config'));
    ['id_csv_url', 'id_kbart_file'].forEach(f => attachFieldRowClass(f, 'csv-config'));
    ['id_marcxml_url'].forEach(f => attachFieldRowClass(f, 'marcxml-config'));
});