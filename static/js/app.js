// API 基础配置
const API_BASE = '';

// ==================== 工具函数 ====================

// 获取 token
function getToken() {
    return localStorage.getItem('token');
}

// 设置 token
function setToken(token) {
    localStorage.setItem('token', token);
}

// 清除 token
function clearToken() {
    localStorage.removeItem('token');
}

// 封装的 API 请求
async function api(url, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            // Token 过期，跳转登录
            clearToken();
            window.location.href = '/';
            return;
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }
        
        return data;
    } catch (error) {
        alert('错误：' + error.message);
        throw error;
    }
}

// ==================== 登录相关 ====================

// 登录表单提交
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const data = await api('/api/v1/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            
            setToken(data.access_token);
            
            // 存储用户信息
            if (data.user) {
                localStorage.setItem('user', JSON.stringify(data.user));
            }
            
            // 跳转到管理页
            window.location.href = '../dashboard.html';
        } catch (error) {
            console.error('登录失败:', error);
        }
    });
}

// 显示注册弹窗
function showRegister() {
    document.getElementById('registerModal').style.display = 'block';
}

// 隐藏注册弹窗
function hideRegister() {
    document.getElementById('registerModal').style.display = 'none';
}

// 注册表单提交
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const password = document.getElementById('reg-password').value;
        const password2 = document.getElementById('reg-password2').value;
        
        if (password !== password2) {
            alert('两次输入的密码不一致');
            return;
        }
        
        const data = {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            password: password
        };
        
        try {
            await api('/api/v1/auth/register', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            alert('注册成功，请登录');
            hideRegister();
        } catch (error) {
            console.error('注册失败:', error);
        }
    });
}

// ==================== 任务管理 ====================

// 加载任务列表
async function loadTasks() {
    try {
        const tasks = await api('/api/v1/tasks/?skip=0&limit=100');
        
        // 更新统计
        updateTaskStats(tasks);
        
        // 渲染表格
        renderTaskTable(tasks);
    } catch (error) {
        console.error('加载任务失败:', error);
    }
}

// 更新任务统计
function updateTaskStats(tasks) {
    const stats = {
        total: tasks.length,
        running: tasks.filter(t => t.status === 'running').length,
        pending: tasks.filter(t => t.status === 'pending').length,
        completed: tasks.filter(t => ['success', 'failed'].includes(t.status)).length
    };
    
    document.getElementById('totalTasks').textContent = stats.total;
    document.getElementById('runningTasks').textContent = stats.running;
    document.getElementById('pendingTasks').textContent = stats.pending;
    document.getElementById('completedTasks').textContent = stats.completed;
}

// 渲染任务表格
function renderTaskTable(tasks) {
    const tbody = document.getElementById('taskTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = tasks.map(task => `
        <tr>
            <td>${task.id}</td>
            <td>${task.name}</td>
            <td>${translateType(task.task_type)}</td>
            <td><span class="status status-${task.status}">${translateStatus(task.status)}</span></td>
            <td><span class="priority priority-${task.priority}">${translatePriority(task.priority)}</span></td>
            <td>${formatDate(task.created_at)}</td>
            <td>
                <button onclick="viewTask(${task.id})" style="margin-right:5px">查看</button>
                <button onclick="deleteTask(${task.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

// 翻译函数
function translateType(type) {
    const map = {
        'one_time': '一次性',
        'scheduled': '定时',
        'recurring': '周期',
        'workflow': '工作流'
    };
    return map[type] || type;
}

function translateStatus(status) {
    const map = {
        'pending': '待执行',
        'running': '运行中',
        'success': '成功',
        'failed': '失败',
        'cancelled': '已取消',
        'timeout': '超时'
    };
    return map[status] || status;
}

function translatePriority(priority) {
    const map = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'critical': '紧急'
    };
    return map[priority] || priority;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN');
}

// 显示创建任务弹窗
function showCreateTask() {
    document.getElementById('createTaskModal').style.display = 'block';
}

// 隐藏创建任务弹窗
function hideCreateTask() {
    document.getElementById('createTaskModal').style.display = 'none';
}

// 创建任务表单提交
if (document.getElementById('createTaskForm')) {
    document.getElementById('createTaskForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            name: document.getElementById('task-name').value,
            task_type: document.getElementById('task-type').value,
            priority: document.getElementById('task-priority').value,
            command: document.getElementById('task-command').value,
            description: document.getElementById('task-desc').value
        };
        
        try {
            await api('/api/v1/tasks/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            alert('任务创建成功');
            hideCreateTask();
            loadTasks(); // 刷新列表
        } catch (error) {
            console.error('创建任务失败:', error);
        }
    });
}

// 查看任务详情
async function viewTask(id) {
    try {
        const task = await api(`/api/v1/tasks/${id}`);
        alert(JSON.stringify(task, null, 2));
    } catch (error) {
        console.error('获取任务详情失败:', error);
    }
}

// 删除任务
async function deleteTask(id) {
    if (!confirm('确定要删除这个任务吗？')) return;
    
    try {
        await api(`/api/v1/tasks/${id}`, {
            method: 'DELETE'
        });
        
        alert('删除成功');
        loadTasks(); // 刷新列表
    } catch (error) {
        console.error('删除任务失败:', error);
    }
}

// ==================== 系统状态 ====================

async function loadSystemInfo() {
    try {
        const info = await api('/api/v1/system/health');
        const container = document.getElementById('systemInfo');
        if (!container) return;
        
        container.innerHTML = `
            <h3>应用信息</h3>
            <p><strong>应用名称：</strong>${info.app_name}</p>
            <p><strong>版本：</strong>${info.version}</p>
            <p><strong>环境：</strong>${info.environment}</p>
            <p><strong>状态：</strong>${info.status === 'healthy' ? '✅ 健康' : '❌ 异常'}</p>
            ${info.timestamp ? `<p><strong>时间：</strong>${formatDate(info.timestamp)}</p>` : ''}
        `;
    } catch (error) {
        console.error('加载系统信息失败:', error);
    }
}

// ==================== Tab 切换 ====================

function showTab(tabName) {
    // 隐藏所有 tab
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });
    
    // 显示指定 tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 加载对应数据
    if (tabName === 'tasks') {
        loadTasks();
    } else if (tabName === 'users') {
        loadUserInfo();
    } else if (tabName === 'system') {
        loadSystemInfo();
    }
}

// ==================== 用户相关 ====================

function logout() {
    clearToken();
    localStorage.removeItem('user');
    window.location.href = '/';
}

// 显示当前用户名
if (document.getElementById('currentUser')) {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.username) {
        document.getElementById('currentUser').textContent = user.username;
    }
}

// ==================== 用户管理 ====================

// 加载用户信息
async function loadUserInfo() {
    try {
        const user = await api('/api/v1/users/me');
        
        // 显示在页面上
        document.getElementById('userUsername').textContent = user.username || '-';
        document.getElementById('userEmail').textContent = user.email || '-';
        document.getElementById('userRole').textContent = user.role || '-';
        document.getElementById('userStatus').textContent = user.status || '-';
        document.getElementById('userCreated').textContent = formatDate(user.created_at);
        
        // 填充编辑表单
        document.getElementById('edit-username').value = user.username || '';
        document.getElementById('edit-email').value = user.email || '';
        document.getElementById('edit-fullname').value = user.full_name || '';
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 更新用户信息
if (document.getElementById('updateProfileForm')) {
    document.getElementById('updateProfileForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            username: document.getElementById('edit-username').value,
            email: document.getElementById('edit-email').value,
            full_name: document.getElementById('edit-fullname').value
        };
        
        try {
            await api('/api/v1/users/me', {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            
            alert('信息更新成功');
            loadUserInfo(); // 刷新显示
        } catch (error) {
            console.error('更新用户信息失败:', error);
        }
    });
}

// 修改密码
if (document.getElementById('changePasswordForm')) {
    document.getElementById('changePasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const oldPassword = document.getElementById('old-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (newPassword !== confirmPassword) {
            alert('两次输入的新密码不一致');
            return;
        }
        
        try {
            await api('/api/v1/users/me/password', {
                method: 'POST',
                body: JSON.stringify({
                    old_password: oldPassword,
                    new_password: newPassword
                })
            });
            
            alert('密码修改成功，请重新登录');
            logout();
        } catch (error) {
            console.error('修改密码失败:', error);
        }
    });
}

// ==================== 系统状态 ====================

async function loadSystemInfo() {
    try {
        // 加载健康状态
        const health = await api('/api/v1/system/health');
        
        document.getElementById('sysName').textContent = health.app_name || '-';
        document.getElementById('sysVersion').textContent = health.version || '-';
        document.getElementById('sysEnv').textContent = health.environment || '-';
        document.getElementById('sysStatus').innerHTML = health.status === 'healthy' 
            ? '<span class="status-success">✅ 健康</span>' 
            : '<span class="status-failed">❌ 异常</span>';
        
    } catch (error) {
        console.error('加载系统信息失败:', error);
    }
}

// 刷新系统信息
function refreshSystemInfo() {
    loadSystemInfo();
    loadTasks();
    alert('刷新完成');
}

// ==================== 初始化 ====================

// 点击弹窗外部关闭
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}