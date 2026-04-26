document.addEventListener('DOMContentLoaded', () => {
    // Tab Switching Logic
    const navLinks = document.querySelectorAll('.nav-links li');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Remove active class from all
            navLinks.forEach(n => n.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            // Add active class to clicked
            link.classList.add('active');
            const targetId = link.getAttribute('data-tab');
            document.getElementById(targetId).classList.add('active');

            // Refresh keys if Evaluate tab is clicked
            if (targetId === 'evaluate-tab') {
                fetchAnswerKeys();
            }
        });
    });

    // Fetch Answer Keys
    async function fetchAnswerKeys() {
        try {
            const res = await fetch('/api/answer-keys/');
            const data = await res.json();
            
            // Update List
            const listEl = document.getElementById('answer-keys-list');
            listEl.innerHTML = '';
            
            // Update Select Dropdown
            const selectEl = document.getElementById('select-answer-key');
            selectEl.innerHTML = '<option value="" disabled selected>Select an answer key...</option>';

            if (data.answer_keys.length === 0) {
                listEl.innerHTML = '<li>No answer keys uploaded yet.</li>';
                return;
            }

            data.answer_keys.forEach(key => {
                // List
                const li = document.createElement('li');
                li.textContent = key;
                listEl.appendChild(li);

                // Select
                const option = document.createElement('option');
                option.value = key;
                option.textContent = key;
                selectEl.appendChild(option);
            });
        } catch (e) {
            console.error("Failed to fetch keys", e);
        }
    }

    // Initial Fetch
    fetchAnswerKeys();

    // Upload Answer Key
    const uploadKeyForm = document.getElementById('upload-key-form');
    uploadKeyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const keyId = document.getElementById('answer-key-id').value;
        const fileInput = document.getElementById('answer-key-file');
        
        if (fileInput.files.length === 0) return;

        const formData = new FormData();
        formData.append('answer_key_id', keyId);
        formData.append('file', fileInput.files[0]);

        const btn = uploadKeyForm.querySelector('button');
        const loader = btn.querySelector('.loader');
        const status = document.getElementById('upload-key-status');

        btn.disabled = true;
        loader.classList.remove('hidden');
        status.textContent = "Uploading and parsing...";
        status.className = "status-msg";

        try {
            const res = await fetch('/api/upload-answer-key/', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (res.ok) {
                status.textContent = `Success! Parsed ${data.parsed_questions_count} questions.`;
                status.classList.add('success');
                uploadKeyForm.reset();
                fetchAnswerKeys(); // Refresh list
            } else {
                status.textContent = `Error: ${data.detail || 'Upload failed'}`;
                status.classList.add('error');
            }
        } catch (err) {
            status.textContent = `Error: ${err.message}`;
            status.classList.add('error');
        } finally {
            btn.disabled = false;
            loader.classList.add('hidden');
        }
    });

    // Evaluate Student Sheet
    const evaluateForm = document.getElementById('evaluate-form');
    evaluateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const keyId = document.getElementById('select-answer-key').value;
        const fileInput = document.getElementById('student-sheet-file');
        
        if (!keyId || fileInput.files.length === 0) return;

        const formData = new FormData();
        // Append all selected files
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('files', fileInput.files[i]);
        }

        const btn = evaluateForm.querySelector('button');
        const loader = btn.querySelector('.loader');
        const status = document.getElementById('evaluate-status');
        const resultsContainer = document.getElementById('results-container');

        btn.disabled = true;
        loader.classList.remove('hidden');
        status.textContent = "Evaluating... This might take a minute.";
        status.className = "status-msg";
        resultsContainer.classList.add('hidden');

        try {
            const res = await fetch(`/api/evaluate/${keyId}`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (res.ok) {
                status.textContent = "Evaluation complete!";
                status.classList.add('success');
                
                renderResults(data.evaluation);
                resultsContainer.classList.remove('hidden');
            } else {
                status.textContent = `Error: ${data.detail || 'Evaluation failed'}`;
                status.classList.add('error');
            }
        } catch (err) {
            status.textContent = `Error: ${err.message}`;
            status.classList.add('error');
        } finally {
            btn.disabled = false;
            loader.classList.add('hidden');
        }
    });

    function renderResults(evaluation) {
        // Update Summary
        document.getElementById('total-score').textContent = evaluation.total_score;
        document.getElementById('max-score').textContent = evaluation.total_max_marks;
        document.getElementById('score-percentage').textContent = `${evaluation.percentage}%`;

        // Update Circle Stroke Dasharray
        const circle = document.getElementById('score-circle-path');
        circle.setAttribute('stroke-dasharray', `${evaluation.percentage}, 100`);

        // Update Color based on score
        if (evaluation.percentage >= 80) circle.style.stroke = "var(--success)";
        else if (evaluation.percentage >= 50) circle.style.stroke = "#f59e0b"; // yellow
        else circle.style.stroke = "var(--danger)";

        // Render Questions
        const qContainer = document.getElementById('question-results');
        qContainer.innerHTML = '';

        evaluation.results.forEach(res => {
            const div = document.createElement('div');
            div.className = 'question-item';
            div.innerHTML = `
                <h4>Question ${res.question_id}</h4>
                <p><strong>Feedback:</strong> ${res.feedback}</p>
                <p><strong>Similarity:</strong> ${(res.similarity * 100).toFixed(1)}%</p>
                <div class="q-score">Score: ${res.score} / ${res.max_marks}</div>
            `;
            qContainer.appendChild(div);
        });
    }
});
