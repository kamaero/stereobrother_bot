// StereoBrother Bot Frontend JavaScript
// Основная логика взаимодействия с API

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация приложения
    initApp();
});

// Основные переменные
let selectedFile = null;
let selectedOption = null;
let currentTaskId = null;
let checkInterval = null;
let isProcessing = false;

// Инициализация приложения
function initApp() {
    console.log('StereoBrother Bot Frontend инициализирован');

    // Проверка статуса системы
    checkSystemStatus();

    // Настройка загрузки файлов
    setupFileUpload();

    // Настройка обработчиков событий
    setupEventListeners();

    // Обновление видимости настроек
    updateSettingsVisibility();
}

// Проверка статуса системы
async function checkSystemStatus() {
    const statusElement = document.getElementById('systemStatus');

    try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
            const data = await response.json();
            statusElement.className = 'status success';
            statusElement.textContent = '✅ Система работает нормально';

            // Показываем дополнительные статусы сервисов
            const services = data.services || {};
            let servicesStatus = '';

            for (const [service, status] of Object.entries(services)) {
                servicesStatus += `${service}: ${status ? '✅' : '❌'}\n`;
            }

            statusElement.title = servicesStatus;
        } else {
            statusElement.className = 'status error';
            statusElement.textContent = '❌ Система недоступна';
        }
    } catch (error) {
        console.error('Ошибка проверки статуса:', error);
        statusElement.className = 'status error';
        statusElement.textContent = '❌ Ошибка подключения к API';
    }
}

// Настройка загрузки файлов
function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const fileInfo = document.getElementById('fileInfo');

    // Обработка выбора файла через кнопку
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop функционал
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
        uploadArea.style.borderColor = '#764ba2';
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = '';
        uploadArea.style.borderColor = '#667eea';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = '';
        uploadArea.style.borderColor = '#667eea';

        if (e.dataTransfer.files.length > 0) {
            handleFileSelect({ target: { files: e.dataTransfer.files } });
        }
    });

    // Клик по области загрузки
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
}

// Обработка выбора файла
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length === 0) return;

    const file = files[0];

    // Проверка типа файла
    if (!file.type.startsWith('audio/')) {
        showError('Пожалуйста, выберите аудио файл');
        return;
    }

    // Проверка размера файла (максимум 100MB)
    if (file.size > 100 * 1024 * 1024) {
        showError('Файл слишком большой. Максимальный размер: 100MB');
        return;
    }

    selectedFile = file;

    // Отображение информации о файле
    displayFileInfo(file);

    // Активация кнопки обработки
    document.getElementById('processBtn').disabled = false;

    // Показываем информацию о файле
    document.getElementById('fileInfo').classList.add('show');

    console.log('Файл выбран:', file.name, file.size, file.type);
}

// Отображение информации о файле
function displayFileInfo(file) {
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileDuration = document.getElementById('fileDuration');

    // Имя файла
    fileName.textContent = `📁 Файл: ${file.name}`;

    // Размер файла
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
    fileSize.textContent = `📊 Размер: ${sizeInMB} MB`;

    // Длительность (будет определена позже)
    fileDuration.textContent = '⏱️ Длительность: определение...';

    // Определение длительности аудио
    const audio = new Audio();
    audio.src = URL.createObjectURL(file);

    audio.addEventListener('loadedmetadata', () => {
        const duration = audio.duration;
        const minutes = Math.floor(duration / 60);
        const seconds = Math.floor(duration % 60);
        fileDuration.textContent = `⏱️ Длительность: ${minutes}:${seconds.toString().padStart(2, '0')}`;

        // Проверка максимальной длительности (10 минут)
        if (duration > 600) {
            showError('Файл слишком длинный. Максимальная длительность: 10 минут');
            selectedFile = null;
            document.getElementById('processBtn').disabled = true;
        }

        URL.revokeObjectURL(audio.src);
    });
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработчики для опций обработки
    document.querySelectorAll('.option').forEach(option => {
        option.addEventListener('click', function() {
            const optionType = this.getAttribute('data-option') ||
                              this.textContent.toLowerCase().includes('улучшение') ? 'enhance' :
                              this.textContent.toLowerCase().includes('очистка') ? 'denoise' :
                              this.textContent.toLowerCase().includes('разделение') ? 'separate' : 'master';

            selectOption(optionType);
        });
    });

    // Обработчик для кнопки обработки
    document.getElementById('processBtn').addEventListener('click', processAudio);

    // Обработчики для настроек
    document.getElementById('intensity').addEventListener('input', function() {
        document.getElementById('intensityValue').textContent = `${this.value}%`;
    });

    // Обработчики для переключения настроек
    document.querySelectorAll('input[name="format"]').forEach(radio => {
        radio.addEventListener('change', updateSettingsVisibility);
    });
}

// Выбор опции обработки
function selectOption(optionType) {
    selectedOption = optionType;

    // Сброс выбора всех опций
    document.querySelectorAll('.option').forEach(opt => {
        opt.classList.remove('selected');
    });

    // Выбор текущей опции
    document.querySelectorAll('.option').forEach(opt => {
        const optType = opt.getAttribute('data-option') ||
                       opt.textContent.toLowerCase().includes('улучшение') ? 'enhance' :
                       opt.textContent.toLowerCase().includes('очистка') ? 'denoise' :
                       opt.textContent.toLowerCase().includes('разделение') ? 'separate' : 'master';

        if (optType === optionType) {
            opt.classList.add('selected');
        }
    });

    // Обновление видимости настроек
    updateSettingsVisibility();

    console.log('Выбрана опция:', optionType);
}

// Обновление видимости настроек
function updateSettingsVisibility() {
    // Скрываем все настройки
    document.querySelectorAll('.settings-section').forEach(section => {
        section.style.display = 'none';
    });

    // Показываем нужные настройки
    if (selectedOption === 'enhance') {
        document.getElementById('enhanceSettings').style.display = 'block';
    } else if (selectedOption === 'denoise') {
        document.getElementById('denoiseSettings').style.display = 'block';
    } else if (selectedOption === 'master') {
        document.getElementById('masterSettings').style.display = 'block';
    }
}

// Обработка аудио
async function processAudio() {
    if (!selectedFile || !selectedOption || isProcessing) {
        showError('Пожалуйста, выберите файл и тип обработки');
        return;
    }

    isProcessing = true;

    // Блокируем кнопку
    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = true;
    processBtn.textContent = 'Обработка...';

    // Показываем прогресс
    const progressContainer = document.getElementById('progressContainer');
    progressContainer.classList.add('show');

    // Скрываем результаты предыдущей обработки
    document.getElementById('resultArea').classList.remove('show');

    try {
        // Шаг 1: Загрузка файла
        updateProgress(10, 'Загрузка файла на сервер...');

        const formData = new FormData();
        formData.append('file', selectedFile);

        // Получаем токен (в реальном приложении здесь была бы аутентификация)
        const token = await getAuthToken();

        const uploadResponse = await fetch('http://localhost:8000/api/audio/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!uploadResponse.ok) {
            throw new Error(`Ошибка загрузки: ${uploadResponse.status}`);
        }

        const uploadResult = await uploadResponse.json();
        currentTaskId = uploadResult.task_id;

        updateProgress(30, 'Файл загружен, начинаем обработку...');

        // Шаг 2: Запуск обработки в зависимости от выбранной опции
        let processResponse;

        if (selectedOption === 'enhance') {
            const mode = document.getElementById('enhanceMode').value;
            processResponse = await startEnhancement(currentTaskId, mode);
        } else if (selectedOption === 'denoise') {
            const noiseTypes = Array.from(document.querySelectorAll('input[name="noiseTypes"]:checked'))
                .map(cb => cb.value);
            const intensity = parseInt(document.getElementById('intensity').value) / 100;
            processResponse = await startDenoising(currentTaskId, noiseTypes, intensity);
        } else if (selectedOption === 'separate') {
            processResponse = await startSeparation(currentTaskId);
        } else if (selectedOption === 'master') {
            const preset = document.getElementById('masterPreset').value;
            const format = document.querySelector('input[name="format"]:checked').value;
            processResponse = await startMastering(currentTaskId, preset, format);
        }

        updateProgress(50, 'Обработка запущена, отслеживаем прогресс...');

        // Шаг 3: Отслеживание прогресса
        await trackProgress(currentTaskId);

    } catch (error) {
        console.error('Ошибка обработки:', error);
        showError(`Ошибка обработки: ${error.message}`);
        resetProcessingState();
    }
}

// Запуск улучшения качества
async function startEnhancement(taskId, mode) {
    const response = await fetch('http://localhost:8000/api/audio/enhance', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: JSON.stringify({
            task_id: taskId,
            mode: mode
        })
    });

    if (!response.ok) {
        throw new Error(`Ошибка улучшения: ${response.status}`);
    }

    return await response.json();
}

// Запуск очистки от шумов
async function startDenoising(taskId, noiseTypes, intensity) {
    const response = await fetch('http://localhost:8000/api/audio/denoise', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: JSON.stringify({
            task_id: taskId,
            noise_types: noiseTypes,
            intensity: intensity
        })
    });

    if (!response.ok) {
        throw new Error(`Ошибка очистки: ${response.status}`);
    }

    return await response.json();
}

// Запуск разделения дорожек
async function startSeparation(taskId) {
    const response = await fetch('http://localhost:8000/api/audio/separate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: JSON.stringify({
            task_id: taskId,
            configuration: 'basic'
        })
    });

    if (!response.ok) {
        throw new Error(`Ошибка разделения: ${response.status}`);
    }

    return await response.json();
}

// Запуск мастеринга
async function startMastering(taskId, preset, format) {
    const response = await fetch('http://localhost:8000/api/audio/master', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: JSON.stringify({
            task_id: taskId,
            preset: preset,
            output_format: format
        })
    });

    if (!response.ok) {
        throw new Error(`Ошибка мастеринга: ${response.status}`);
    }

    return await response.json();
}

// Отслеживание прогресса задачи
async function trackProgress(taskId) {
    return new Promise((resolve, reject) => {
        let progress = 50;

        checkInterval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/audio/task/${taskId}`, {
                    headers: {
                        'Authorization': `Bearer ${await getAuthToken()}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`Ошибка получения статуса: ${response.status}`);
                }

                const taskStatus = await response.json();

                // Обновляем прогресс
                if (taskStatus.progress > progress) {
                    progress = taskStatus.progress * 100;
                    updateProgress(progress, getStatusMessage(taskStatus.status));
                }

                // Проверяем завершение
                if (taskStatus.status === 'completed') {
                    clearInterval(checkInterval);
                    updateProgress(100, 'Обработка завершена!');

                    // Показываем результаты
                    setTimeout(() => {
                        showResults(taskStatus);
                        resetProcessingState();
                        resolve();
                    }, 1000);

                } else if (taskStatus.status === 'failed') {
                    clearInterval(checkInterval);
                    showError(`Ошибка обработки: ${taskStatus.error_message || 'Неизвестная ошибка'}`);
                    resetProcessingState();
                    reject(new Error('Обработка завершилась с ошибкой'));
                }

            } catch (error) {
                console.error('Ошибка отслеживания прогресса:', error);
                clearInterval(checkInterval);
                showError('Ошибка отслеживания прогресса');
                resetProcessingState();
                reject(error);
            }
        }, 2000); // Проверяем каждые 2 секунды
    });
}

// Получение токена аутентификации
async function getAuthToken() {
    // В демо-режиме используем тестовый токен
    // В реальном приложении здесь была бы логика аутентификации
    return 'demo-token-for-testing';
}

// Обновление прогресса
function updateProgress(percent, message) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const statusMessage = document.getElementById('statusMessage');

    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${Math.round(percent)}%`;
    statusMessage.textContent = message;

    console.log(`Прогресс: ${percent}% - ${message}`);
}

// Получение сообщения о статусе
function getStatusMessage(status) {
    const messages = {
        'pending': 'Задача в очереди...',
        'processing': 'Идет обработка...',
        'completed': 'Обработка завершена!',
        'failed': 'Ошибка обработки'
    };

    return messages[status] || 'Обработка...';
}

// Показать результаты
function showResults(taskStatus) {
    const resultArea = document.getElementById('resultArea');
    const resultsList = document.getElementById('resultsList');

    // Очищаем предыдущие результаты
    resultsList.innerHTML = '';

    // Создаем элементы результатов
    if (taskStatus.result_url) {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        resultItem.innerHTML = `
            <span>Обработанный файл</span>
            <a href="${taskStatus.result_url}" target="_blank" download>
                <i class="fas fa-download"></i> Скачать
            </a>
        `;
        resultsList.appendChild(resultItem);
    }

    if (taskStatus.result_urls) {
        for (const [track, url] of Object.entries(taskStatus.result_urls)) {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.innerHTML = `
                <span>${getTrackName(track)}</span>
                <a href="${url}" target="_blank" download>
                    <i class="fas fa-download"></i> Скачать
                </a>
            `;
            resultsList.appendChild(resultItem);
        }
    }

    // Показываем область результатов
    resultArea.classList.add('show');
}

// Получение читаемого имени дорожки
function getTrackName(trackKey) {
    const track
