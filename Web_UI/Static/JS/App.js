/**
 * DST TORRENT WEB UI APPLICATION
 * JAVASCRIPT FRONTEND LOGIC FOR TORRENT MANAGEMENT
 * DARK GREEN RETRO THEME
 */

// API BASE URL
const API_BASE = window.location.origin;

// GLOBAL STATE
let Current_Tab = 'Dashboard_Tab';
let Refresh_Interval = null;
let System_Start_Time = Date.now();
let Current_Modal_Torrent_Hash = null;
let Confirm_Callback = null;

/**
 * INITIALIZE APPLICATION ON PAGE LOAD
 */
document.addEventListener('DOMContentLoaded', function() {
    Initialize_UI();
    Setup_Event_Listeners();
    Start_Auto_Refresh();
    Show_Notification('SYSTEM INITIALIZED', 'success');
});

/**
 * INITIALIZE UI COMPONENTS
 */
function Initialize_UI() {
    // LOAD INITIAL DATA
    Refresh_Dashboard();
    Refresh_System_Config();
}

/**
 * SETUP EVENT LISTENERS FOR TABS AND FORMS
 */
function Setup_Event_Listeners() {
    // TAB NAVIGATION
    const Tab_Buttons = document.querySelectorAll('.tab-btn');
    Tab_Buttons.forEach(button => {
        button.addEventListener('click', function() {
            const Tab_ID = this.getAttribute('data-tab');
            Switch_Tab(Tab_ID);
        });
    });

    // UPLOAD FORM
    const Upload_Form = document.getElementById('Upload_Form');
    if (Upload_Form) {
        Upload_Form.addEventListener('submit', Handle_Upload);
    }

    // DOWNLOAD FORM
    const Download_Form = document.getElementById('Download_Form');
    if (Download_Form) {
        Download_Form.addEventListener('submit', Handle_Download);
    }

    // DEAD DROP FORMS
    const DeadDrop_Form = document.getElementById('DeadDrop_Form');
    if (DeadDrop_Form) {
        DeadDrop_Form.addEventListener('submit', Handle_DeadDrop_Create);
    }

    const DeadDrop_Access_Form = document.getElementById('DeadDrop_Access_Form');
    if (DeadDrop_Access_Form) {
        DeadDrop_Access_Form.addEventListener('submit', Handle_DeadDrop_Access);
    }

    // MODAL CLOSE ON BACKGROUND CLICK
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
    });

    // FILE INPUT CHANGE LISTENERS
    const File_Input = document.getElementById('File_Input');
    if (File_Input) {
        File_Input.addEventListener('change', function() {
            Update_File_Name_Display('File_Input', 'File_Input_Name');
        });
    }

    const DeadDrop_File = document.getElementById('DeadDrop_File');
    if (DeadDrop_File) {
        DeadDrop_File.addEventListener('change', function() {
            Update_File_Name_Display('DeadDrop_File', 'DeadDrop_File_Name');
        });
    }

    const Download_DST_File = document.getElementById('Download_DST_File');
    if (Download_DST_File) {
        Download_DST_File.addEventListener('change', function() {
            Update_File_Name_Display('Download_DST_File', 'Download_DST_File_Name');
        });
    }

    // CSP-Safe Action Wiring: Use Event Delegation For Data-Action Elements
    document.addEventListener('click', function(e) {
        const elem = e.target.closest('[data-action]');
        if (!elem) return;

        const action = elem.dataset.action;
        const target = elem.dataset.target;
        const argsRaw = elem.dataset.args;
        if (!action) return;

        if (action === 'triggerFile' && target) {
            const inp = document.getElementById(target);
            if (inp) inp.click();
            return;
        }

        let args = [];
        if (argsRaw) {
            args = argsRaw.split('|');
        }

        if (target && args.length === 0) {
            args = [target];
        }

        const fn = window[action];
        if (typeof fn === 'function') {
            try {
                fn(...args);
            } catch (err) {
                console.error('Error Executing Action', action, err);
            }
        } else {
            console.warn('No Function Found For Data-Action:', action);
        }
    });
}

/**
 * SWITCH BETWEEN TABS
 */
function Switch_Tab(Tab_ID) {
    // HIDE ALL TABS
    const All_Tabs = document.querySelectorAll('.tab-content');
    All_Tabs.forEach(tab => tab.classList.remove('active'));

    // DEACTIVATE ALL BUTTONS
    const All_Buttons = document.querySelectorAll('.tab-btn');
    All_Buttons.forEach(btn => btn.classList.remove('active'));

    // SHOW SELECTED TAB
    const Selected_Tab = document.getElementById(Tab_ID);
    if (Selected_Tab) {
        Selected_Tab.classList.add('active');
    }

    // ACTIVATE SELECTED BUTTON
    const Selected_Button = document.querySelector(`[data-tab="${Tab_ID}"]`);
    if (Selected_Button) {
        Selected_Button.classList.add('active');
    }

    Current_Tab = Tab_ID;

    // LOAD TAB-SPECIFIC DATA
    switch(Tab_ID) {
        case 'Dashboard_Tab':
            Refresh_Dashboard();
            break;
        case 'Torrents_Tab':
            Refresh_Torrents();
            break;
        case 'Download_Tab':
            Refresh_Downloads();
            break;
        case 'DeadDrop_Tab':
            Refresh_DeadDrops();
            break;
        case 'Peers_Tab':
            Refresh_Peers();
            break;
        case 'Blockchain_Tab':
            Refresh_Blockchain();
            break;
        case 'System_Tab':
            Refresh_System();
            break;
    }
}

/**
 * START AUTO-REFRESH TIMER
 */
function Start_Auto_Refresh() {
    // REFRESH EVERY 5 SECONDS
    Refresh_Interval = setInterval(() => {
        Update_Uptime();
        if (Current_Tab === 'Dashboard_Tab') {
            Refresh_Dashboard();
        } else if (Current_Tab === 'Download_Tab') {
            Refresh_Downloads();
        } else if (Current_Tab === 'Peers_Tab') {
            Refresh_Peers();
        } else if (Current_Tab === 'Blockchain_Tab') {
            Refresh_Blockchain();
        } else if (Current_Tab === 'System_Tab') {
            Refresh_System();
        }
    }, 5000);
}

/**
 * UPDATE SYSTEM UPTIME
 */
function Update_Uptime() {
    const Uptime_MS = Date.now() - System_Start_Time;
    const Uptime_Seconds = Math.floor(Uptime_MS / 1000);
    const Hours = Math.floor(Uptime_Seconds / 3600);
    const Minutes = Math.floor((Uptime_Seconds % 3600) / 60);
    const Seconds = Uptime_Seconds % 60;
    
    const Uptime_String = `${String(Hours).padStart(2, '0')}:${String(Minutes).padStart(2, '0')}:${String(Seconds).padStart(2, '0')}`;
    
    const Uptime_Element = document.getElementById('System_Uptime');
    if (Uptime_Element) {
        Uptime_Element.textContent = Uptime_String;
    }
}

/**
 * REFRESH DASHBOARD DATA
 */
async function Refresh_Dashboard() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_Dashboard"]');
    if (btn) {
        const originalText = btn.textContent;
        btn.textContent = 'REFRESHING...';
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/stats`);
        if (Response.ok) {
            const Data = await Response.json();
            Update_Dashboard(Data);
            Show_Notification('DASHBOARD REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH DASHBOARD:', error);
        Show_Notification('FAILED TO LOAD DASHBOARD DATA', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.textContent = 'REFRESH DASHBOARD';
            btn.disabled = false;
        }
    }
}

/**
 * UPDATE DASHBOARD WITH DATA
 */
function Update_Dashboard(Data) {
    // UPDATE STATISTICS
    Set_Text_If_Exists('Total_Torrents', Data.Total_Torrents || 0);
    Set_Text_If_Exists('Active_Peers', Data.Active_Peers || 0);
    Set_Text_If_Exists('Total_Uploads', Data.Total_Uploads || 0);
    Set_Text_If_Exists('Total_Downloads', Data.Total_Downloads || 0);
    Set_Text_If_Exists('Data_Shared', Format_Bytes(Data.Data_Shared || 0));

    // UPDATE ACTIVITY LOG
    if (Data.Recent_Activity && Data.Recent_Activity.length > 0) {
        const Log_Container = document.getElementById('Activity_Log');
        if (Log_Container) {
            Log_Container.innerHTML = '';
            Data.Recent_Activity.forEach(activity => {
                const Log_Entry = document.createElement('div');
                Log_Entry.className = 'log-entry';
                Log_Entry.textContent = activity.toUpperCase();
                Log_Container.appendChild(Log_Entry);
            });
        }
    }
}

/**
 * REFRESH TORRENTS LIST
 */
async function Refresh_Torrents() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_Torrents"]');
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/torrents`);
        if (Response.ok) {
            const Data = await Response.json();
            Display_Torrents(Data.Torrents || []);
            Show_Notification('TORRENT LIST REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH TORRENTS:', error);
        Show_Notification('FAILED TO LOAD TORRENTS', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
}

/**
 * DISPLAY TORRENTS IN LIST
 */
function Display_Torrents(Torrents) {
    const Torrent_Container = document.getElementById('Torrent_List');
    if (!Torrent_Container) return;

    if (Torrents.length === 0) {
        Torrent_Container.innerHTML = `
            <div class="wallet-card">
                <div class="wallet-info">
                    <div class="wallet-name">NO TORRENTS AVAILABLE</div>
                    <div class="wallet-address">UPLOAD A FILE TO CREATE YOUR FIRST TORRENT</div>
                </div>
            </div>
        `;
        return;
    }

    Torrent_Container.innerHTML = '';
    Torrents.forEach(torrent => {
        const Torrent_Card = document.createElement('div');
        Torrent_Card.className = 'wallet-card';
        Torrent_Card.innerHTML = `
            <div class="wallet-info">
                <div class="wallet-name">${Escape_HTML(torrent.Name || 'UNKNOWN')}</div>
                <div class="wallet-address">HASH: ${Escape_HTML(torrent.Info_Hash || 'N/A')}</div>
                <div class="wallet-address">SIZE: ${Format_Bytes(torrent.Size || 0)} | SEEDERS: ${torrent.Seeders || 0} | LEECHERS: ${torrent.Leechers || 0}</div>
            </div>
            <div class="wallet-balance">
                <button class="btn btn-primary btn-small" data-action="Show_Torrent_Details" data-args="${Escape_HTML(torrent.Info_Hash)}">DETAILS</button>
                <button class="btn btn-success btn-small" data-action="Download_Torrent_By_Hash" data-args="${Escape_HTML(torrent.Info_Hash)}">GET .DST</button>
                <button class="btn btn-warning btn-small" data-action="Start_Seeding" data-args="${Escape_HTML(torrent.Info_Hash)}|${Escape_HTML(torrent.Name)}">SEED</button>
            </div>
        `;
        Torrent_Container.appendChild(Torrent_Card);
    });
}

/**
 * HANDLE FILE UPLOAD FORM SUBMISSION
 */
async function Handle_Upload(event) {
    event.preventDefault();

    const File_Input = document.getElementById('File_Input');
    const Torrent_Name = document.getElementById('Torrent_Name').value;
    const Description = document.getElementById('Description').value;
    const Tracker_URL = document.getElementById('Tracker_URL').value;
    const Piece_Size = document.getElementById('Piece_Size').value;
    const Enable_Encryption = document.getElementById('Enable_Encryption').value;

    if (!File_Input.files.length) {
        Show_Notification('PLEASE SELECT A FILE', 'error');
        return;
    }

    const Form_Data = new FormData();
    Form_Data.append('file', File_Input.files[0]);
    Form_Data.append('name', Torrent_Name);
    Form_Data.append('description', Description);
    Form_Data.append('tracker_url', Tracker_URL);
    Form_Data.append('piece_size', Piece_Size);
    Form_Data.append('enable_encryption', Enable_Encryption);

    try {
        Show_Upload_Progress('UPLOADING FILE...');
        
        const Response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: Form_Data
        });

        if (Response.ok) {
            const Data = await Response.json();
            Show_Notification('TORRENT CREATED SUCCESSFULLY', 'success');
            Show_Upload_Progress(`TORRENT CREATED: ${Data.Info_Hash || 'SUCCESS'}`);
            
            // RESET FORM
            document.getElementById('Upload_Form').reset();
            
            // SWITCH TO TORRENTS TAB
            setTimeout(() => {
                Switch_Tab('Torrents_Tab');
            }, 2000);
        } else if (Response.status === 409) {
            // TORRENT ALREADY EXISTS
            const Data = await Response.json();
            Show_Notification('TORRENT ALREADY EXISTS', 'warning');
            Show_Upload_Progress(`DUPLICATE TORRENT: ${Data.Name} (${Data.Info_Hash.substring(0, 8)}...)`);
            
            // RESET FORM BUT KEEP FILE NAME FOR REFERENCE
            document.getElementById('Upload_Form').reset();
        } else {
            const Error = await Response.json();
            Show_Notification(`UPLOAD FAILED: ${Error.message || 'UNKNOWN ERROR'}`, 'error');
            Show_Upload_Progress(`ERROR: ${Error.message || 'UPLOAD FAILED'}`);
        }
    } catch (error) {
        console.error('UPLOAD ERROR:', error);
        Show_Notification('UPLOAD FAILED: NETWORK ERROR', 'error');
        Show_Upload_Progress('ERROR: NETWORK ERROR');
    }
}

/**
 * HANDLE DOWNLOAD FORM SUBMISSION
 */
async function Handle_Download(event) {
    event.preventDefault();

    const DST_File_Input = document.getElementById('Download_DST_File');
    const Download_Directory = document.getElementById('Download_Directory_Input').value;

    if (!DST_File_Input.files.length) {
        Show_Notification('PLEASE SELECT A .DST FILE', 'error');
        return;
    }

    const DST_File = DST_File_Input.files[0];

    try {
        Show_Notification('STARTING DOWNLOAD...', 'info');
        Show_Download_Progress('INITIALIZING DOWNLOAD...');

        // Prepare Form Data
        const Form_Data = new FormData();
        Form_Data.append('dst_file', DST_File);
        if (Download_Directory) {
            Form_Data.append('download_directory', Download_Directory);
        }

        // Start Download
        const Response = await fetch(`${API_BASE}/api/download/start`, {
            method: 'POST',
            body: Form_Data
        });

        if (Response.ok) {
            const Data = await Response.json();
            Show_Notification('DOWNLOAD STARTED SUCCESSFULLY', 'success');
            Show_Download_Progress('DOWNLOAD STARTED - CHECKING PROGRESS BELOW');

            // Show stop button
            document.getElementById('Stop_Download_Btn').style.display = 'inline-block';

            // Refresh downloads list
            setTimeout(() => {
                Refresh_Downloads();
            }, 1000);

        } else {
            const Error = await Response.json();
            Show_Notification(`DOWNLOAD FAILED: ${Error.message || 'UNKNOWN ERROR'}`, 'error');
            Show_Download_Progress(`ERROR: ${Error.message || 'DOWNLOAD FAILED'}`);
        }
    } catch (error) {
        console.error('DOWNLOAD ERROR:', error);
        Show_Notification('DOWNLOAD FAILED: NETWORK ERROR', 'error');
        Show_Download_Progress('ERROR: NETWORK ERROR');
    }
}

/**
 * REFRESH DOWNLOADS LIST AND STATUS
 */
async function Refresh_Downloads() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_Downloads"]');
    if (btn) {
        const originalText = btn.textContent;
        btn.textContent = 'REFRESHING...';
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/downloads/status`);
        if (Response.ok) {
            const Data = await Response.json();
            Display_Active_Downloads(Data.downloads || []);
            Show_Notification('DOWNLOAD STATUS REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH DOWNLOADS:', error);
        Show_Notification('FAILED TO LOAD DOWNLOAD STATUS', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.textContent = 'REFRESH STATUS';
            btn.disabled = false;
        }
    }
}

/**
 * STOP ALL DOWNLOADS
 */
async function Stop_All_Downloads() {
    try {
        Show_Notification('STOPPING ALL DOWNLOADS...', 'info');

        const Response = await fetch(`${API_BASE}/api/downloads/stop`, {
            method: 'POST'
        });

        if (Response.ok) {
            Show_Notification('ALL DOWNLOADS STOPPED', 'success');
            Show_Download_Progress('ALL DOWNLOADS STOPPED');

            // Hide stop button
            document.getElementById('Stop_Download_Btn').style.display = 'none';

            // Refresh downloads list
            setTimeout(() => {
                Refresh_Downloads();
            }, 1000);
        } else {
            Show_Notification('FAILED TO STOP DOWNLOADS', 'error');
        }
    } catch (error) {
        console.error('STOP DOWNLOADS ERROR:', error);
        Show_Notification('FAILED TO STOP DOWNLOADS', 'error');
    }
}

/**
 * DISPLAY ACTIVE DOWNLOADS
 */
function Display_Active_Downloads(Downloads) {
    const Container = document.getElementById('Active_Downloads_List');
    if (!Container) return;

    if (Downloads.length === 0) {
        Container.innerHTML = `
            <div class="wallet-card">
                <div class="wallet-info">
                    <div class="wallet-name">NO ACTIVE DOWNLOADS</div>
                    <div class="wallet-address">START A DOWNLOAD TO SEE IT HERE</div>
                </div>
            </div>
        `;
        return;
    }

    Container.innerHTML = '';
    Downloads.forEach(download => {
        const Progress_Percent = download.progress || 0;
        const Status_Class = download.status === 'completed' ? 'success' :
                           download.status === 'error' ? 'danger' : 'warning';

        const Download_Card = document.createElement('div');
        Download_Card.className = 'wallet-card';
        Download_Card.innerHTML = `
            <div class="wallet-info">
                <div class="wallet-name">${Escape_HTML(download.name || 'UNKNOWN')}</div>
                <div class="wallet-address">HASH: ${Escape_HTML(download.info_hash || 'N/A')}</div>
                <div class="wallet-address">SIZE: ${Format_Bytes(download.total_size || 0)} | DOWNLOADED: ${Format_Bytes(download.downloaded || 0)}</div>
                <div class="wallet-address">PEERS: ${download.peers || 0} | SPEED: ${Format_Bytes(download.speed || 0)}/s</div>
            </div>
            <div class="wallet-balance">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Progress_Percent}%"></div>
                    <div class="progress-text">${Progress_Percent.toFixed(1)}%</div>
                </div>
                <div class="status-indicator ${Status_Class}">${(download.status || 'unknown').toUpperCase()}</div>
            </div>
        `;
        Container.appendChild(Download_Card);
    });
}

/**
 * SHOW DOWNLOAD PROGRESS MESSAGE
 */
function Show_Download_Progress(Message) {
    const Progress_Container = document.getElementById('Download_Progress_Log');
    if (Progress_Container) {
        const Timestamp = new Date().toLocaleTimeString();
        Progress_Container.innerHTML = `<div class="log-entry">[${Timestamp}] ${Message}</div>` + Progress_Container.innerHTML;
    }
}

/**
 * SHOW UPLOAD PROGRESS MESSAGE
 */
function Show_Upload_Progress(Message) {
    const Progress_Container = document.getElementById('Upload_Progress');
    if (Progress_Container) {
        const Log_Entry = document.createElement('div');
        Log_Entry.className = 'log-entry';
        Log_Entry.textContent = Message.toUpperCase();
        Progress_Container.appendChild(Log_Entry);
        
        // SCROLL TO BOTTOM
        Progress_Container.scrollTop = Progress_Container.scrollHeight;
    }
}

/**
 * DOWNLOAD TORRENT BY HASH
 */
async function Download_Torrent_By_Hash(Info_Hash, Config = {}) {
    try {
        Show_Notification('DOWNLOADING TORRENT FILE...', 'info');

        // Build URL with optional download path
        let Download_URL = `${API_BASE}/api/download/${Info_Hash}`;
        if (Config.torrent_dir) {
            Download_URL += `?download_path=${encodeURIComponent(Config.torrent_dir)}`;
        }

        const Response = await fetch(Download_URL);

        if (Response.ok) {
            // Get filename from response headers or use default
            const Content_Disposition = Response.headers.get('Content-Disposition');
            let Filename = `${Info_Hash}.dst`;

            if (Content_Disposition) {
                const Filename_Match = Content_Disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (Filename_Match && Filename_Match[1]) {
                    Filename = Filename_Match[1].replace(/['"]/g, '');
                }
            }

            const Blob = await Response.blob();
            const URL = window.URL.createObjectURL(Blob);
            const Link = document.createElement('a');
            Link.href = URL;
            Link.download = Filename;
            document.body.appendChild(Link);
            Link.click();
            document.body.removeChild(Link);
            window.URL.revokeObjectURL(URL);

            Show_Notification(`TORRENT FILE DOWNLOADED: ${Filename}`, 'success');

            // Show Instructions For Next Steps
            setTimeout(() => {
                Show_Notification('USE A TORRENT CLIENT TO DOWNLOAD THE ACTUAL FILES', 'info');
            }, 2000);

        } else if (Response.status === 404) {
            Show_Notification('TORRENT NOT FOUND', 'error');
        } else {
            const Error_Data = await Response.json().catch(() => ({}));
            Show_Notification(`DOWNLOAD FAILED: ${Error_Data.message || 'UNKNOWN ERROR'}`, 'error');
        }
    } catch (error) {
        console.error('DOWNLOAD ERROR:', error);
        Show_Notification('DOWNLOAD FAILED: NETWORK ERROR', 'error');
    }
}

/**
 * START SEEDING A TORRENT
 */
async function Start_Seeding(Info_Hash, Torrent_Name) {
    try {
        Show_Notification('STARTING SEEDING PROCESS...', 'info');
        
        // Get Directory Settings
        const Torrent_Dir = Get_Directory_Setting('Torrent_Directory', 'Torrents');
        const Download_Dir = Get_Directory_Setting('Download_Directory', 'Downloads');
        
        // Prompt For Torrent File Location
        const Torrent_Path = prompt(`LOCATE .DST TORRENT FILE FOR "${Torrent_Name}":`, `${Torrent_Dir}/${Info_Hash}.dst`);
        if (Torrent_Path === null) return; // User cancelled
        
        // Prompt For Download/Content Location
        const Download_Path = prompt(`LOCATE DOWNLOADED CONTENT FOR "${Torrent_Name}":`, Download_Dir);
        if (Download_Path === null) return; // User cancelled
        
        // Confirm Seeding Start
        const Confirm_Message = `
START SEEDING CONFIRMATION:
• Torrent: ${Torrent_Name}
• .dst File: ${Torrent_Path}
• Content: ${Download_Path}

THIS WILL MAKE YOUR FILES AVAILABLE TO OTHER PEERS.
CONTINUE?`;
        
        if (!confirm(Confirm_Message)) return;
        
        // Prepare Form Data
        const Form_Data = new FormData();
        Form_Data.append('torrent_path', Torrent_Path);
        Form_Data.append('download_path', Download_Path);
        
        // Start Seeding
        const Response = await fetch(`${API_BASE}/api/seed/${Info_Hash}`, {
            method: 'POST',
            body: Form_Data
        });
        
        if (Response.ok) {
            const Data = await Response.json();
            Show_Notification('SEEDING STARTED SUCCESSFULLY', 'success');
            
            // Refresh Torrents To Update Seeder Count
            setTimeout(() => {
                Refresh_Torrents();
            }, 1000);
        } else {
            const Error = await Response.json();
            Show_Notification(`SEEDING FAILED: ${Error.message || 'UNKNOWN ERROR'}`, 'error');
        }
    } catch (error) {
        console.error('SEEDING ERROR:', error);
        Show_Notification('SEEDING FAILED: NETWORK ERROR', 'error');
    }
}

/**
 * GET DIRECTORY SETTING WITH FALLBACK
 */
function Get_Directory_Setting(Key, Default_Value) {
    return localStorage.getItem(Key) || Default_Value;
}

/**
 * BROWSE DIRECTORY - OPEN FOLDER PICKER
 */
async function Browse_Directory(Directory_Type) {
    try {
        // Try Modern File System Access API First (Chrome/Edge)
        if ('showDirectoryPicker' in window) {
            const Dir_Handle = await window.showDirectoryPicker();
            const Dir_Path = Dir_Handle.name; // This Gives Us The Folder Name, Not Full Path
            
            // For Security Reasons, Browsers Don't Expose Full Paths
            // We'll Show A Message Explaining This Limitation
            Show_Notification('FOLDER SELECTED: ' + Dir_Path, 'success');
            
            // Update The Input Field With The Selected Folder Name
            const Input_Element = document.getElementById(Directory_Type);
            if (Input_Element) {
                Input_Element.value = Dir_Path;
            }
            
            // Store The Handle For Potential Future Use
            localStorage.setItem(Directory_Type + '_Handle', JSON.stringify(Dir_Handle));
            
            return;
        }
        
        // Fallback: Try webkitdirectory (Chrome/Safari)
        if (document.webkitdirectory !== undefined) {
            // Create A Temporary File Input For Directory Selection
            const Temp_Input = document.createElement('input');
            Temp_Input.type = 'file';
            Temp_Input.webkitdirectory = true;
            Temp_Input.className = 'hidden-file';
            
            Temp_Input.onchange = function(e) {
                if (e.target.files.length > 0) {
                    // Get The Directory Path From The First File
                    const File_Path = e.target.files[0].webkitRelativePath;
                    const Dir_Path = File_Path.split('/')[0];
                    
                    Show_Notification('FOLDER SELECTED: ' + Dir_Path, 'success');
                    
                    const Input_Element = document.getElementById(Directory_Type);
                    if (Input_Element) {
                        Input_Element.value = Dir_Path;
                    }
                }
            };
            
            document.body.appendChild(Temp_Input);
            Temp_Input.click();
            document.body.removeChild(Temp_Input);
            return;
        }
        
        // Final Fallback: Manual Entry With Helpful Message
        const Current_Value = document.getElementById(Directory_Type).value || '';
        const Example_Path = Directory_Type === 'Download_Directory' ? 'C:\\Downloads' :
                           Directory_Type === 'Upload_Directory' ? 'C:\\Uploads' :
                           Directory_Type === 'Temp_Directory' ? 'C:\\Temp' :
                           Directory_Type === 'Torrent_Directory' ? 'C:\\Torrents' : 'C:\\MyFolder';
        
        const User_Path = prompt(
            `ENTER ${Directory_Type.replace('_', ' ').toUpperCase()} PATH:\n\n` +
            `Example: ${Example_Path}\n\n` +
            `Current: ${Current_Value || 'Not Set'}\n\n` +
            `Note: Your Browser Doesn't Support Folder Selection.\n` +
            `Please Enter The Full Path Manually.`
        );
        
        if (User_Path !== null && User_Path.trim() !== '') {
            const Input_Element = document.getElementById(Directory_Type);
            if (Input_Element) {
                Input_Element.value = User_Path.trim();
                Show_Notification('PATH SET: ' + User_Path.trim(), 'success');
            }
        }
        
    } catch (error) {
        console.error('BROWSE DIRECTORY ERROR:', error);
        
        // If User Cancelled Or Error Occurred, Show Manual Entry
        const Current_Value = document.getElementById(Directory_Type).value || '';
        const Example_Path = Directory_Type === 'Download_Directory' ? 'C:\\Downloads' :
                           Directory_Type === 'Upload_Directory' ? 'C:\\Uploads' :
                           Directory_Type === 'Temp_Directory' ? 'C:\\Temp' :
                           Directory_Type === 'Torrent_Directory' ? 'C:\\Torrents' : 'C:\\MyFolder';
        
        const User_Path = prompt(
            `ENTER ${Directory_Type.replace('_', ' ').toUpperCase()} PATH:\n\n` +
            `Example: ${Example_Path}\n\n` +
            `Current: ${Current_Value || 'Not Set'}\n\n` +
            `Please Enter The Full Path Manually.`
        );
        
        if (User_Path !== null && User_Path.trim() !== '') {
            const Input_Element = document.getElementById(Directory_Type);
            if (Input_Element) {
                Input_Element.value = User_Path.trim();
                Show_Notification('PATH SET: ' + User_Path.trim(), 'success');
            }
        }
    }
}

/**
 * DOWNLOAD TORRENT (PROMPT FOR HASH)
 */
function Download_Torrent() {
    const Info_Hash = prompt('ENTER TORRENT INFO HASH:');
    if (Info_Hash) {
        // Ask About Download Location
        const Download_Dir = Get_Directory_Setting('Download_Directory', 'Downloads');
        const Confirmed_Download_Dir = prompt('DOWNLOAD DIRECTORY (Where Torrent Files Will Be Saved):', Download_Dir);
        if (Confirmed_Download_Dir === null) return; // User Cancelled
        
        // Ask About Torrent File Location
        const Torrent_Dir = Get_Directory_Setting('Torrent_Directory', 'Torrents');
        const Confirmed_Torrent_Dir = prompt('TORRENT FILE DIRECTORY (Where .dst File Will Be Saved):', Torrent_Dir);
        if (Confirmed_Torrent_Dir === null) return; // User Cancelled
        
        // Ask About Temp Directory
        const Temp_Dir = Get_Directory_Setting('Temp_Directory', 'Temp');
        const Confirmed_Temp_Dir = prompt('TEMP DIRECTORY (For Processing):', Temp_Dir);
        if (Confirmed_Temp_Dir === null) return; // User Cancelled
        
        // Show Summary Of Choices
        const Summary = `
DOWNLOAD CONFIGURATION:
• Torrent Files: ${Confirmed_Download_Dir}
• .dst File: ${Confirmed_Torrent_Dir}  
• Temp Files: ${Confirmed_Temp_Dir}

PROCEED WITH DOWNLOAD?`;
        
        if (confirm(Summary)) {
            Download_Torrent_By_Hash(Info_Hash, {
                download_dir: Confirmed_Download_Dir,
                torrent_dir: Confirmed_Torrent_Dir,
                temp_dir: Confirmed_Temp_Dir
            });
        }
    }
}

/**
 * REFRESH PEERS LIST
 */
async function Refresh_Peers() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_Peers"]');
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/peers`);
        if (Response.ok) {
            const Data = await Response.json();
            Display_Peers(Data.Peers || []);
            Update_Peer_Stats(Data);
            Show_Notification('PEER LIST REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH PEERS:', error);
        Show_Notification('FAILED TO LOAD PEERS', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
}

/**
 * DISPLAY PEERS IN LIST
 */
function Display_Peers(Peers) {
    const Peer_Container = document.getElementById('Peer_List');
    if (!Peer_Container) return;

    if (Peers.length === 0) {
        Peer_Container.innerHTML = `
            <div class="peer-item">
                <span class="peer-url">NO PEERS CONNECTED</span>
                <span class="peer-status dead">OFFLINE</span>
            </div>
        `;
        return;
    }

    Peer_Container.innerHTML = '';
    Peers.forEach(peer => {
        const Peer_Item = document.createElement('div');
        Peer_Item.className = 'peer-item';
    Peer_Item.classList.add('clickable');
    Peer_Item.onclick = () => Show_Peer_Details(peer.Peer_Id || 'UNKNOWN', peer.IP || 'UNKNOWN', peer.Port || 0);
        Peer_Item.innerHTML = `
            <span class="peer-url">${Escape_HTML(peer.IP || 'UNKNOWN')}:${peer.Port || 0}</span>
            <span class="peer-status ${peer.Is_Active ? 'alive' : 'dead'}">${peer.Is_Active ? 'ONLINE' : 'OFFLINE'}</span>
        `;
        Peer_Container.appendChild(Peer_Item);
    });
}

/**
 * UPDATE PEER STATISTICS
 */
function Update_Peer_Stats(Data) {
    Set_Text_If_Exists('Connected_Peers', Data.Total_Peers || 0);
    Set_Text_If_Exists('Total_Seeders', Data.Total_Seeders || 0);
    Set_Text_If_Exists('Total_Leechers', Data.Total_Leechers || 0);
    Set_Text_If_Exists('Upload_Speed', `${Format_Bytes(Data.Upload_Speed || 0)}/S`);
}

/**
 * DISCOVER NEW PEERS
 */
async function Discover_Peers() {
    try {
        Show_Notification('DISCOVERING PEERS...', 'info');
        const Response = await fetch(`${API_BASE}/api/peers/discover`, {
            method: 'POST'
        });
        
        if (Response.ok) {
            Show_Notification('PEER DISCOVERY INITIATED', 'success');
            setTimeout(Refresh_Peers, 2000);
        } else {
            Show_Notification('PEER DISCOVERY FAILED', 'error');
        }
    } catch (error) {
        console.error('PEER DISCOVERY ERROR:', error);
        Show_Notification('PEER DISCOVERY FAILED', 'error');
    }
}

/**
 * REFRESH BLOCKCHAIN DATA
 */
async function Refresh_Blockchain() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_Blockchain"]');
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/blockchain`);
        if (Response.ok) {
            const Data = await Response.json();
            Update_Blockchain(Data);
            Show_Notification('BLOCKCHAIN REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH BLOCKCHAIN:', error);
        Show_Notification('FAILED TO LOAD BLOCKCHAIN', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
}

/**
 * UPDATE BLOCKCHAIN DISPLAY
 */
function Update_Blockchain(Data) {
    Set_Text_If_Exists('Chain_Length', Data.Chain_Length || 0);
    Set_Text_If_Exists('Pending_Transactions', Data.Pending_Transactions || 0);
    Set_Text_If_Exists('Mining_Difficulty', Data.Difficulty || 4);
    Set_Text_If_Exists('Last_Block_Time', Data.Last_Block_Time || 'N/A');

    // DISPLAY BLOCKS
    if (Data.Blocks && Data.Blocks.length > 0) {
        const Blocks_Container = document.getElementById('Blockchain_Blocks');
        if (Blocks_Container) {
            Blocks_Container.innerHTML = '';
            Data.Blocks.forEach(block => {
                const Block_Entry = document.createElement('div');
                Block_Entry.className = 'log-entry';
                Block_Entry.textContent = `BLOCK #${block.Index || 0} | HASH: ${(block.Hash || '').substring(0, 16)}... | TRANSACTIONS: ${block.Transactions || 0}`;
                Blocks_Container.appendChild(Block_Entry);
            });
        }
    }
}

/**
 * MINE A NEW BLOCK
 */
async function Mine_Block() {
    try {
        Show_Notification('MINING BLOCK...', 'info');
        const Response = await fetch(`${API_BASE}/api/blockchain/mine`, {
            method: 'POST'
        });
        
        if (Response.ok) {
            const Data = await Response.json();
            Show_Notification(`BLOCK MINED: ${Data.Block_Hash || 'SUCCESS'}`, 'success');
            setTimeout(Refresh_Blockchain, 1000);
        } else {
            Show_Notification('MINING FAILED', 'error');
        }
    } catch (error) {
        console.error('MINING ERROR:', error);
        Show_Notification('MINING FAILED', 'error');
    }
}

/**
 * REFRESH SYSTEM DATA
 */
async function Refresh_System() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_System"]');
    if (btn) {
        const originalText = btn.textContent;
        btn.textContent = 'REFRESHING...';
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/system/health`);
        if (Response.ok) {
            const Data = await Response.json();
            Update_System(Data);
            Show_Notification('SYSTEM STATUS REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH SYSTEM:', error);
        Show_Notification('FAILED TO LOAD SYSTEM STATUS', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.textContent = 'REFRESH SYSTEM';
            btn.disabled = false;
        }
    }
}

/**
 * UPDATE SYSTEM DISPLAY
 */
function Update_System(Data) {
    Set_Text_If_Exists('CPU_Usage', `${Data.CPU_Usage || 0}%`);
    Set_Text_If_Exists('Memory_Usage', `${Data.Memory_Usage || 0}%`);
    Set_Text_If_Exists('Disk_Usage', `${Data.Disk_Usage || 0}%`);
    Set_Text_If_Exists('Network_Status', Data.Network_Status || 'ONLINE');

    // UPDATE SYSTEM LOGS
    if (Data.Logs && Data.Logs.length > 0) {
        const Logs_Container = document.getElementById('System_Logs');
        if (Logs_Container) {
            Logs_Container.innerHTML = '';
            Data.Logs.forEach(log => {
                const Log_Entry = document.createElement('div');
                Log_Entry.className = 'log-entry';
                Log_Entry.textContent = log.toUpperCase();
                Logs_Container.appendChild(Log_Entry);
            });
        }
    }
}

/**
 * REFRESH SYSTEM CONFIG
 */
async function Refresh_System_Config() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_System_Config"]');
    if (btn) {
        const originalText = btn.textContent;
        btn.textContent = 'REFRESHING...';
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/config`);
        if (Response.ok) {
            const Data = await Response.json();
            Update_System_Config(Data);
            Show_Notification('SYSTEM CONFIG REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH CONFIG:', error);
        Show_Notification('FAILED TO LOAD SYSTEM CONFIG', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.textContent = 'REFRESH CONFIG';
            btn.disabled = false;
        }
    }
}

/**
 * UPDATE SYSTEM CONFIG DISPLAY
 */
function Update_System_Config(Data) {
    Set_Text_If_Exists('Server_Host', Data.Host || '0.0.0.0');
    Set_Text_If_Exists('Server_Port', Data.Port || 5043);
    Set_Text_If_Exists('Encryption_Status', Data.Encryption || 'AES-256-GCM');
    Set_Text_If_Exists('Quantum_Status', Data.Quantum_Resistant ? 'ENABLED' : 'DISABLED');
    Set_Text_If_Exists('Database_Type', Data.Database || 'SQLITE');
    Set_Text_If_Exists('System_Version', Data.Version || '1.0.0');
    
    // Load Directory Settings From Local Storage
    Load_Directory_Settings();
}

/**
 * SHOW NOTIFICATION
 */
function Show_Notification(Message, Type = 'info') {
    const Container = document.getElementById('Notification_Container');
    if (!Container) return;

    const Notification = document.createElement('div');
    Notification.className = `notification ${Type}`;
    Notification.textContent = Message.toUpperCase();
    
    Container.appendChild(Notification);

    // AUTO-REMOVE AFTER 5 SECONDS
    setTimeout(() => {
        Notification.remove();
    }, 5000);
}

/**
 * UTILITY: SET TEXT IF ELEMENT EXISTS
 */
function Set_Text_If_Exists(Element_ID, Text) {
    const Element = document.getElementById(Element_ID);
    if (Element) {
        Element.textContent = Text;
    }
}

/**
 * UTILITY: SET VALUE IF ELEMENT EXISTS (For Input Elements)
 */
function Set_Value_If_Exists(Element_ID, Value) {
    const Element = document.getElementById(Element_ID);
    if (Element) {
        try {
            Element.value = Value;
        } catch (e) {
            // If Element Doesn't Support Value, Ignore
        }
    }
}

/**
 * UTILITY: FORMAT BYTES TO READABLE SIZE
 */
function Format_Bytes(Bytes) {
    if (Bytes === 0) return '0 B';
    const K = 1024;
    const Sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const I = Math.floor(Math.log(Bytes) / Math.log(K));
    return Math.round(Bytes / Math.pow(K, I) * 100) / 100 + ' ' + Sizes[I];
}

/**
 * UTILITY: ESCAPE HTML
 */
function Escape_HTML(Text) {
    const Map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(Text).replace(/[&<>"']/g, m => Map[m]);
}

// ═══════════════════════════════════════════════════════════════════════
// MODAL FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════

/**
 * OPEN MODAL
 */
function Open_Modal(Modal_ID) {
    const Modal = document.getElementById(Modal_ID);
    if (Modal) {
        Modal.classList.remove('hidden');
    }
}

/**
 * CLOSE MODAL
 */
function Close_Modal(Modal_ID) {
    const Modal = document.getElementById(Modal_ID);
    if (Modal) {
        Modal.classList.add('hidden');
    }
}

/**
 * SHOW TORRENT DETAILS MODAL
 */
function Show_Torrent_Details(Info_Hash) {
    // FETCH TORRENT DETAILS
    fetch(`${API_BASE}/api/torrents/${Info_Hash}`)
        .then(response => response.json())
        .then(data => {
            Current_Modal_Torrent_Hash = Info_Hash;
            
            Set_Text_If_Exists('Modal_Torrent_Name', data.Name || 'UNKNOWN');
            Set_Text_If_Exists('Modal_Torrent_Hash', Info_Hash);
            Set_Text_If_Exists('Modal_Torrent_Size', Format_Bytes(data.Size || 0));
            Set_Text_If_Exists('Modal_Torrent_PieceSize', Format_Bytes(data.Piece_Size || 0));
            Set_Text_If_Exists('Modal_Torrent_Created', data.Created || 'N/A');
            Set_Text_If_Exists('Modal_Torrent_Seeders', data.Seeders || 0);
            Set_Text_If_Exists('Modal_Torrent_Leechers', data.Leechers || 0);
            Set_Text_If_Exists('Modal_Torrent_Downloads', data.Downloaded || 0);
            
            Open_Modal('Torrent_Details_Modal');
        })
        .catch(error => {
            console.error('FAILED TO LOAD TORRENT DETAILS:', error);
            Show_Notification('FAILED TO LOAD TORRENT DETAILS', 'error');
        });
}

/**
 * DOWNLOAD TORRENT FROM MODAL
 */
function Download_Modal_Torrent() {
    if (Current_Modal_Torrent_Hash) {
        Download_Torrent_By_Hash(Current_Modal_Torrent_Hash);
        Close_Modal('Torrent_Details_Modal');
    }
}

/**
 * SHOW PEER DETAILS MODAL
 */
function Show_Peer_Details(Peer_ID, IP, Port) {
    Set_Text_If_Exists('Modal_Peer_ID', Peer_ID);
    Set_Text_If_Exists('Modal_Peer_IP', IP);
    Set_Text_If_Exists('Modal_Peer_Port', Port);
    Set_Text_If_Exists('Modal_Peer_Status', 'ONLINE');
    Set_Text_If_Exists('Modal_Peer_Type', 'UNKNOWN');
    Set_Text_If_Exists('Modal_Peer_Uploaded', '0 B');
    Set_Text_If_Exists('Modal_Peer_Downloaded', '0 B');
    Set_Text_If_Exists('Modal_Peer_LastSeen', 'JUST NOW');
    
    Open_Modal('Peer_Details_Modal');
}

/**
 * SHOW CONFIRM MODAL
 */
function Show_Confirm_Modal(Message, Callback) {
    Set_Text_If_Exists('Confirm_Message', Message.toUpperCase());
    Confirm_Callback = Callback;
    Open_Modal('Confirm_Modal');
}

/**
 * CONFIRM ACTION
 */
function Confirm_Action() {
    if (Confirm_Callback && typeof Confirm_Callback === 'function') {
        Confirm_Callback();
        Confirm_Callback = null;
    }
    Close_Modal('Confirm_Modal');
}

// ═══════════════════════════════════════════════════════════════════════
// DEAD DROP FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════

/**
 * HANDLE DEAD DROP CREATION
 */
async function Handle_DeadDrop_Create(event) {
    event.preventDefault();

    const File_Input = document.getElementById('DeadDrop_File');
    const Name = document.getElementById('DeadDrop_Name').value;
    const Password = document.getElementById('DeadDrop_Password').value;
    const Expiration = document.getElementById('DeadDrop_Expiration').value;
    const Max_Downloads = document.getElementById('DeadDrop_MaxDownloads').value;

    if (!File_Input.files.length) {
        Show_Notification('PLEASE SELECT A FILE', 'error');
        return;
    }

    if (!Password || Password.length < 8) {
        Show_Notification('PASSWORD MUST BE AT LEAST 8 CHARACTERS', 'error');
        return;
    }

    const Form_Data = new FormData();
    Form_Data.append('file', File_Input.files[0]);
    Form_Data.append('name', Name || 'ANONYMOUS');
    Form_Data.append('password', Password);
    Form_Data.append('expiration_hours', Expiration);
    Form_Data.append('max_downloads', Max_Downloads);

    try {
        Show_Notification('CREATING DEAD DROP...', 'info');
        
        const Response = await fetch(`${API_BASE}/api/deaddrop/create`, {
            method: 'POST',
            body: Form_Data
        });

        if (Response.ok) {
            const Data = await Response.json();
            
            // SHOW SUCCESS MODAL WITH DROP INFO
            Set_Text_If_Exists('Modal_Drop_ID', Data.Drop_ID || 'ERROR');
            Set_Text_If_Exists('Modal_Drop_URL', `${API_BASE}/deaddrop/${Data.Drop_ID}`);
            Set_Text_If_Exists('Modal_Drop_Expires', Data.Expires || 'N/A');
            Set_Text_If_Exists('Modal_Drop_MaxDownloads', Max_Downloads === '0' ? 'UNLIMITED' : Max_Downloads);
            
            Open_Modal('DeadDrop_Success_Modal');
            Show_Notification('DEAD DROP CREATED SUCCESSFULLY', 'success');
            
            // RESET FORM
            document.getElementById('DeadDrop_Form').reset();
            
            // REFRESH LIST
            setTimeout(Refresh_DeadDrops, 2000);
        } else {
            const Error = await Response.json();
            Show_Notification(`FAILED: ${Error.message || 'UNKNOWN ERROR'}`, 'error');
        }
    } catch (error) {
        console.error('DEAD DROP CREATE ERROR:', error);
        Show_Notification('FAILED TO CREATE DEAD DROP', 'error');
    }
}

/**
 * HANDLE DEAD DROP ACCESS
 */
async function Handle_DeadDrop_Access(event) {
    event.preventDefault();

    const Drop_ID = document.getElementById('DeadDrop_ID').value;
    const Password = document.getElementById('DeadDrop_Access_Password').value;

    if (!Drop_ID || !Password) {
        Show_Notification('PLEASE PROVIDE DROP ID AND PASSWORD', 'error');
        return;
    }

    try {
        Show_Notification('ACCESSING DEAD DROP...', 'info');
        
        const Response = await fetch(`${API_BASE}/api/deaddrop/access`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                drop_id: Drop_ID,
                password: Password
            })
        });

        if (Response.ok) {
            // DOWNLOAD FILE
            const Blob = await Response.blob();
            const URL = window.URL.createObjectURL(Blob);
            const Link = document.createElement('a');
            Link.href = URL;
            Link.download = `DeadDrop_${Drop_ID}`;
            document.body.appendChild(Link);
            Link.click();
            document.body.removeChild(Link);
            window.URL.revokeObjectURL(URL);
            
            Show_Notification('DEAD DROP ACCESSED SUCCESSFULLY', 'success');
            
            // RESET FORM
            document.getElementById('DeadDrop_Access_Form').reset();
        } else {
            const Error = await Response.json();
            Show_Notification(`ACCESS FAILED: ${Error.message || 'INVALID CREDENTIALS'}`, 'error');
        }
    } catch (error) {
        console.error('DEAD DROP ACCESS ERROR:', error);
        Show_Notification('FAILED TO ACCESS DEAD DROP', 'error');
    }
}

/**
 * REFRESH DEAD DROPS LIST
 */
async function Refresh_DeadDrops() {
    // Visual Feedback
    const btn = document.querySelector('[data-action="Refresh_DeadDrops"]');
    if (btn) {
        btn.classList.add('loading');
        btn.disabled = true;
    }

    try {
        const Response = await fetch(`${API_BASE}/api/deaddrop/list`);
        if (Response.ok) {
            const Data = await Response.json();
            Display_DeadDrops(Data.Drops || []);
            Show_Notification('DEAD DROP LIST REFRESHED', 'success');
        }
    } catch (error) {
        console.error('FAILED TO REFRESH DEAD DROPS:', error);
        Show_Notification('FAILED TO LOAD DEAD DROPS', 'error');
    } finally {
        // Restore Button
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }
}

/**
 * DISPLAY DEAD DROPS IN LIST
 */
function Display_DeadDrops(Drops) {
    const Container = document.getElementById('DeadDrop_List');
    if (!Container) return;

    if (Drops.length === 0) {
        Container.innerHTML = `
            <div class="wallet-card">
                <div class="wallet-info">
                    <div class="wallet-name">NO ACTIVE DEAD DROPS</div>
                    <div class="wallet-address">CREATE A DEAD DROP TO SEE IT HERE</div>
                </div>
            </div>
        `;
        return;
    }

    Container.innerHTML = '';
    Drops.forEach(drop => {
        const Drop_Card = document.createElement('div');
        Drop_Card.className = 'wallet-card';
        Drop_Card.innerHTML = `
            <div class="wallet-info">
                <div class="wallet-name">${Escape_HTML(drop.Name || 'ANONYMOUS DROP')}</div>
                <div class="wallet-address">ID: ${Escape_HTML(drop.Drop_ID || 'N/A')}</div>
                <div class="wallet-address">EXPIRES: ${drop.Expires || 'N/A'} | DOWNLOADS: ${drop.Downloads || 0}/${drop.Max_Downloads === 0 ? '∞' : drop.Max_Downloads}</div>
            </div>
            <div class="wallet-balance">
                <button class="btn btn-danger btn-small" data-action="Delete_DeadDrop" data-args="${Escape_HTML(drop.Drop_ID)}">DELETE</button>
            </div>
        `;
        Container.appendChild(Drop_Card);
    });
}

/**
 * DELETE DEAD DROP
 */
function Delete_DeadDrop(Drop_ID) {
    Show_Confirm_Modal('DELETE THIS DEAD DROP? THIS ACTION CANNOT BE UNDONE!', async () => {
        try {
            const Response = await fetch(`${API_BASE}/api/deaddrop/delete/${Drop_ID}`, {
                method: 'DELETE'
            });
            
            if (Response.ok) {
                Show_Notification('DEAD DROP DELETED', 'success');
                Refresh_DeadDrops();
            } else {
                Show_Notification('FAILED TO DELETE DEAD DROP', 'error');
            }
        } catch (error) {
            console.error('DELETE ERROR:', error);
            Show_Notification('FAILED TO DELETE DEAD DROP', 'error');
        }
    });
}

/**
 * COPY DROP ID TO CLIPBOARD
 */
function Copy_Drop_ID() {
    const Drop_ID = document.getElementById('Modal_Drop_ID').textContent;
    navigator.clipboard.writeText(Drop_ID)
        .then(() => Show_Notification('DROP ID COPIED TO CLIPBOARD', 'success'))
        .catch(() => Show_Notification('FAILED TO COPY', 'error'));
}

/**
 * COPY DROP URL TO CLIPBOARD
 */
function Copy_Drop_URL() {
    const Drop_URL = document.getElementById('Modal_Drop_URL').textContent;
    navigator.clipboard.writeText(Drop_URL)
        .then(() => Show_Notification('URL COPIED TO CLIPBOARD', 'success'))
        .catch(() => Show_Notification('FAILED TO COPY', 'error'));
}

/**
 * UPDATE FILE NAME DISPLAY FOR CUSTOM FILE INPUTS
 */
function Update_File_Name_Display(Input_ID, Display_ID) {
    const File_Input = document.getElementById(Input_ID);
    const File_Display = document.getElementById(Display_ID);

    if (File_Input && File_Display) {
        if (File_Input.files.length > 0) {
            File_Display.textContent = File_Input.files[0].name.toUpperCase();
        } else {
            File_Display.textContent = 'NO FILE CHOSEN';
        }
    }
}

/**
 * LOAD DIRECTORY SETTINGS FROM LOCAL STORAGE
 */
function Load_Directory_Settings() {
    const Directories = {
        'Download_Directory': 'Downloads',
        'Upload_Directory': 'Uploads', 
        'Temp_Directory': 'Temp',
        'Torrent_Directory': 'Torrents'
    };
    
    for (const [Key, Default_Value] of Object.entries(Directories)) {
        const Saved_Value = localStorage.getItem(Key) || Default_Value;
        Set_Value_If_Exists(Key, Saved_Value);
    }
    
    // Update Directory Displays
    Update_Directory_Displays();
}

/**
 * SAVE DIRECTORY SETTING TO LOCAL STORAGE
 */
function Save_Directory_Setting(Setting_Key) {
    const Input_Element = document.getElementById(Setting_Key);
    if (Input_Element) {
        const Directory_Path = Input_Element.value.trim();
        if (Directory_Path) {
            // Basic Validation - Check If It Looks Like A Valid Path
            if (Directory_Path.length > 3 && (Directory_Path.includes('\\') || Directory_Path.includes('/'))) {
                localStorage.setItem(Setting_Key, Directory_Path);
                Show_Notification(`${Setting_Key.replace('_', ' ').toUpperCase()} SAVED`, 'success');
                // Update Directory Displays If Any Directory Setting Changed
                Update_Directory_Displays();
            } else {
                Show_Notification('PLEASE ENTER A VALID DIRECTORY PATH', 'error');
            }
        } else {
            Show_Notification('PLEASE ENTER A DIRECTORY PATH', 'error');
        }
    }
}

/**
 * UPDATE DIRECTORY DISPLAYS WITH CURRENT SETTINGS
 */
function Update_Directory_Displays() {
    const Upload_Dir = localStorage.getItem('Upload_Directory') || 'Uploads';
    const Temp_Dir = localStorage.getItem('Temp_Directory') || 'Temp';
    const Torrent_Dir = localStorage.getItem('Torrent_Directory') || 'Torrents';
    const Download_Dir = localStorage.getItem('Download_Directory') || 'CDownloads';
    
    // Update Upload Info
    Set_Text_If_Exists('Upload_Info_Dir', Upload_Dir);
    Set_Text_If_Exists('Temp_Info_Dir', Temp_Dir);
    Set_Text_If_Exists('Torrent_Info_Dir', Torrent_Dir);
    
    // Update Download Info
    Set_Text_If_Exists('Download_Info_Dir_Display', Download_Dir);
    Set_Text_If_Exists('Torrent_Download_Info_Dir', Torrent_Dir);
}

