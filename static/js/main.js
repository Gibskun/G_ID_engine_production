// Global JavaScript utilities for G_ID Management System

class GIDSystemAPI {
    constructor(baseURL = '/gid/api/v1') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed: ${url}`, error);
            throw error;
        }
    }

    // Dashboard API
    async getDashboard() {
        return await this.request('/dashboard');
    }

    // Records API
    async getRecords(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/records?${queryString}`);
    }

    async getRecordsCount(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/records/count?${queryString}`);
    }

    async getRecord(gid) {
        return await this.request(`/records/${gid}`);
    }

    // Enhanced data viewer API for multiple tables
    async getTableData(tableName, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/data/${tableName}?${queryString}`);
    }

    async getTableCount(tableName, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/data/${tableName}/count?${queryString}`);
    }

    // Sync API
    async initialSync() {
        return await this.request('/sync/initial', { method: 'POST' });
    }

    async incrementalSync() {
        return await this.request('/sync/incremental', { method: 'POST' });
    }

    async getSyncStatus() {
        return await this.request('/sync/status');
    }

    // Excel Upload API
    async uploadExcel(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return await this.request('/upload/excel', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
    }

    // Advanced Workflow Upload API
    async uploadFileAdvanced(file, enableDeactivation = true) {
        const formData = new FormData();
        formData.append('file', file);
        
        const url = `/upload/advanced?enable_deactivation=${enableDeactivation}`;
        
        return await this.request(url, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
    }

    // Advanced Workflow Sync API
    async syncPegawaiAdvanced() {
        return await this.request('/sync/pegawai-advanced', { method: 'POST' });
    }

    // Workflow Status API
    async getWorkflowStatus() {
        return await this.request('/workflow/status');
    }

    async getExcelTemplate() {
        return await this.request('/excel/template');
    }

    // G_ID API
    async previewNextGID() {
        return await this.request('/gid/next-preview');
    }

    async validateGID(gid) {
        return await this.request(`/gid/validate/${gid}`);
    }

    // Monitoring API
    async getMonitoringStatus() {
        return await this.request('/monitoring/status');
    }

    async startMonitoring(type = 'polling') {
        return await this.request(`/monitoring/start?monitor_type=${type}`, { method: 'POST' });
    }

    async stopMonitoring() {
        return await this.request('/monitoring/stop', { method: 'POST' });
    }

    // Audit API
    async getAuditLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/audit/logs?${queryString}`);
    }

    // Health check
    async healthCheck() {
        return await this.request('/health');
    }
}

// Global API instance
const api = new GIDSystemAPI();

// Utility functions
class UIUtils {
    static showAlert(message, type = 'info', duration = 5000) {
        const alertContainer = document.getElementById('alert-container') || this.createAlertContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <span>${message}</span>
            <button type="button" class="modal-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        alertContainer.appendChild(alert);
        
        if (duration > 0) {
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.remove();
                }
            }, duration);
        }
        
        return alert;
    }

    static createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1001; max-width: 400px;';
        document.body.appendChild(container);
        return container;
    }

    static showLoading(element, text = 'Loading...') {
        const loadingSpinner = '<span class="loading"></span>';
        if (element.tagName === 'BUTTON') {
            element.dataset.originalText = element.innerHTML;
            element.innerHTML = `${loadingSpinner}${text}`;
            element.disabled = true;
        } else {
            element.dataset.originalHTML = element.innerHTML;
            element.innerHTML = `<div class="text-center">${loadingSpinner}${text}</div>`;
        }
    }

    static hideLoading(element) {
        if (element.tagName === 'BUTTON') {
            element.innerHTML = element.dataset.originalText || 'Submit';
            element.disabled = false;
            delete element.dataset.originalText;
        } else {
            element.innerHTML = element.dataset.originalHTML || '';
            delete element.dataset.originalHTML;
        }
    }

    static formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    static createStatusBadge(status) {
        const className = status === 'Active' ? 'status-active' : 'status-inactive';
        return `<span class="status-badge ${className}">${status}</span>`;
    }

    static createSourceBadge(source) {
        const className = source === 'database_pegawai' ? 'source-database' : 'source-excel';
        const displayText = source === 'database_pegawai' ? 'Database' : 'Excel';
        return `<span class="status-badge ${className}">${displayText}</span>`;
    }

    static createModal(title, content, options = {}) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <span class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</span>
                </div>
                <div class="modal-content">
                    ${content}
                </div>
                ${options.buttons ? `<div class="modal-footer">${options.buttons}</div>` : ''}
            </div>
        `;

        document.body.appendChild(modal);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        return modal;
    }

    static updateProgressBar(percentage, text = '') {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            bar.style.width = `${percentage}%`;
            bar.textContent = text || `${percentage}%`;
        });
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(() => {
            this.showAlert('Failed to copy to clipboard', 'danger', 3000);
        });
    }
}

// Pagination utility
class Pagination {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.currentPage = options.currentPage || 1;
        this.pageSize = options.pageSize || 50;
        this.totalItems = options.totalItems || 0;
        this.onPageChange = options.onPageChange || (() => {});
    }

    render() {
        if (!this.container) return;

        const totalPages = Math.ceil(this.totalItems / this.pageSize);
        
        if (totalPages <= 1) {
            this.container.innerHTML = '';
            return;
        }

        let paginationHTML = '<div class="pagination">';
        
        // Previous button
        paginationHTML += `
            <button ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="pagination.goToPage(${this.currentPage - 1})">
                Previous
            </button>
        `;

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            paginationHTML += `<button onclick="pagination.goToPage(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += '<span>...</span>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="${i === this.currentPage ? 'active' : ''}" 
                        onclick="pagination.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHTML += '<span>...</span>';
            }
            paginationHTML += `<button onclick="pagination.goToPage(${totalPages})">${totalPages}</button>`;
        }

        // Next button
        paginationHTML += `
            <button ${this.currentPage === totalPages ? 'disabled' : ''} 
                    onclick="pagination.goToPage(${this.currentPage + 1})">
                Next
            </button>
        `;

        paginationHTML += '</div>';
        this.container.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.totalItems / this.pageSize);
        if (page < 1 || page > totalPages) return;
        
        this.currentPage = page;
        this.render();
        this.onPageChange(page);
    }

    updateTotal(totalItems) {
        this.totalItems = totalItems;
        this.render();
    }
}

// File upload utility
class FileUploader {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            accept: options.accept || '.xlsx,.xls',
            maxSize: options.maxSize || 10 * 1024 * 1024, // 10MB
            onUpload: options.onUpload || (() => {}),
            onError: options.onError || ((error) => UIUtils.showAlert(error, 'danger'))
        };
        
        this.init();
    }

    init() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="file-upload-area" ondrop="fileUploader.handleDrop(event)" 
                 ondragover="fileUploader.handleDragOver(event)" 
                 ondragleave="fileUploader.handleDragLeave(event)"
                 onclick="document.getElementById('file-input').click()">
                <div class="file-upload-icon">📁</div>
                <p><strong>Click to select file</strong> or drag and drop</p>
                <p class="text-muted">Supported formats: ${this.options.accept}</p>
                <p class="text-muted">Maximum size: ${this.formatSize(this.options.maxSize)}</p>
            </div>
            <input type="file" id="file-input" style="display: none" 
                   accept="${this.options.accept}" onchange="fileUploader.handleFileSelect(event)">
        `;
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.currentTarget.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(event) {
        const files = event.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        // Validate file type
        if (!this.isValidFileType(file.name)) {
            this.options.onError(`Invalid file type. Supported types: ${this.options.accept}`);
            return;
        }

        // Validate file size
        if (file.size > this.options.maxSize) {
            this.options.onError(`File too large. Maximum size: ${this.formatSize(this.options.maxSize)}`);
            return;
        }

        this.options.onUpload(file);
    }

    isValidFileType(filename) {
        const acceptedTypes = this.options.accept.split(',').map(type => type.trim());
        const fileExtension = '.' + filename.split('.').pop().toLowerCase();
        return acceptedTypes.includes(fileExtension);
    }

    formatSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Initialize common functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Highlight current page in navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Initialize tooltips (if any)
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.title = element.dataset.tooltip;
    });
});

// Export utilities for use in other files
window.GIDSystemAPI = GIDSystemAPI;
window.UIUtils = UIUtils;
window.Pagination = Pagination;
window.FileUploader = FileUploader;
window.api = api;