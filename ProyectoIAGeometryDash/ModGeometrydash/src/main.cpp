#include <Geode/Geode.hpp>
#include <Geode/modify/PlayLayer.hpp>
#include <fstream>
#include <filesystem>

using namespace geode::prelude;

static std::ofstream g_TempLogFile;
const std::filesystem::path AI_LOG_DIR = std::filesystem::current_path() / "geode" / "logs";
const std::filesystem::path AI_LOG_TEMP = AI_LOG_DIR / "gd_ai_log_temp.log";
const std::filesystem::path AI_LOG_FINAL = AI_LOG_DIR / "gd_ai_log.log";

void openTempLog() {
    if (g_TempLogFile.is_open()) g_TempLogFile.close();
    std::filesystem::create_directories(AI_LOG_TEMP.parent_path());
    g_TempLogFile.open(AI_LOG_TEMP, std::ios::out | std::ios::trunc);
}

void writeTempLog(const std::string& text) {
    if (g_TempLogFile.is_open()) {
        g_TempLogFile << text << "\n";
        g_TempLogFile.flush();
    }
}

void saveLogAsFinal() {
    if (std::filesystem::exists(AI_LOG_TEMP)) {
        try {
            std::filesystem::copy_file(AI_LOG_TEMP, AI_LOG_FINAL, std::filesystem::copy_options::overwrite_existing);
        } catch(...) {}
    }
}

// 0: Aire, 1: Sólido, 2: Mortal
int scanPoint(float x, float y, CCArray* objects) {
    if (!objects) return 0;
    CCObject* objPtr;
    CCARRAY_FOREACH(objects, objPtr) {
        GameObject* obj = dynamic_cast<GameObject*>(objPtr);
        if (!obj) continue;
        
        // Verificar visibilidad (en lugar de m_active que no existe)
        if (!obj->isVisible()) continue;
        
        // Optimización de rango X
        if (obj->getPositionX() < x - 20.0f || obj->getPositionX() > x + 20.0f) continue;

        CCRect hitbox = obj->getObjectRect();
        // Punto de escaneo pequeño
        if (hitbox.intersectsRect(CCRect(x - 4, y - 4, 8, 8))) {
            int id = obj->m_objectID;
            
            // Detección de Pinchos y Sierras (IDs específicos)
            // 8: Spike básico
            // 39: Spike grande
            // 103, 392, 393, 667, 1705: Otros spikes
            // 88, 89, 397-399, 1619: Saws (sierras)
            if (id == 8 || id == 39 || id == 103 || id == 392 || id == 393 || 
                id == 667 || id == 1705 || id == 88 || id == 89 || 
                id == 397 || id == 398 || id == 399 || id == 1619) {
                return 2; // MORTAL
            }
            
            // Portales y Orbes (IDs específicos - NO son sólidos)
            // Portales: 10-13, 45-47, 99, 101, 111, 200-203, 286-287, 660, 745-747, 1331
            // Orbes: 36, 84, 140-141, 1022, 1333
            // Pads: 35, 67, 1332
            if (id == 10 || id == 11 || id == 12 || id == 13 || 
                id == 45 || id == 46 || id == 47 || 
                id == 99 || id == 101 || id == 111 || 
                id == 200 || id == 201 || id == 202 || id == 203 || 
                id == 286 || id == 287 || id == 660 || 
                id == 745 || id == 746 || id == 747 || id == 1331 ||
                id == 36 || id == 84 || id == 140 || id == 141 || 
                id == 1022 || id == 1333 || id == 35 || id == 67 || id == 1332) {
                return 0; // Portales/Orbes - Ignorar como aire
            }
            
            return 1; // Sólido (bloques, plataformas)
        }
    }
    return 0; // Aire
}

class $modify(MyPlayLayer, PlayLayer) {
public:
    struct Fields {
        float timeElapsed = 0.0f;
        CCPoint lastPlayerPos = {0.0f, 0.0f};
    };

    bool init(GJGameLevel* level, bool useReplay, bool dontCreateObjects) {
        if (!PlayLayer::init(level, useReplay, dontCreateObjects)) return false;
        openTempLog();
        writeTempLog("SESSION_START");
        this->schedule(schedule_selector(MyPlayLayer::updateBot));
        return true;
    }

    void updateBot(float dt) {
        if (!m_player1 || !m_objects) return;

        auto playerPos = m_player1->getPosition();
        float px = playerPos.x;
        float py = playerPos.y;
        
        // Optimización: Solo escribir si avanzó
        auto f = m_fields.self();
        if (px <= f->lastPlayerPos.x + 0.5f && px > 10.0f) return;
        f->lastPlayerPos = playerPos;

        // --- MATRIX VISION (3 Alturas x 5 Distancias) ---
        // Alturas relativas:
        // -20 (Suelo/Huecos)
        // +0  (Centro/Frente)
        // +30 (Cabeza/Aéreo)
        
        std::string matrixData = "";
        
        for (int i = 1; i <= 5; i++) {
            float dist = i * 30.0f; // 30, 60, 90, 120, 150
            float checkX = px + dist;
            
            int valLow  = scanPoint(checkX, py - 20.0f, m_objects);
            int valMid  = scanPoint(checkX, py, m_objects);
            int valHigh = scanPoint(checkX, py + 30.0f, m_objects);
            
            // Formato: L,M,H,
            matrixData += fmt::format("{},{},{},", valLow, valMid, valHigh);
        }

        // STATE|X|Y|Vel|G|GridMatrix...
        std::string logLine = fmt::format("STATE|{:.1f}|{:.1f}|{:.1f}|{}|{}", 
            px, py, m_player1->m_yVelocity, m_player1->m_isOnGround ? 1 : 0, matrixData);
        
        writeTempLog(logLine);
    }

    void destroyPlayer(PlayerObject* player, GameObject* object) {
        PlayLayer::destroyPlayer(player, object);
        writeTempLog("DEATH");
        saveLogAsFinal();
    }

    void levelComplete() {
        PlayLayer::levelComplete();
        writeTempLog("WIN");
        saveLogAsFinal();
    }
};