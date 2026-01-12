/*
 * Dragino SX1302 - Set Custom Sync Word
 *
 * Kompilierung:
 *   scp dragino_set_syncword.c root@10.0.0.2:/tmp/
 *   ssh root@10.0.0.2 "cd /tmp && gcc dragino_set_syncword.c -o set_syncword -lloragw"
 *
 * Ausführung:
 *   ssh root@10.0.0.2 "killall fwd; /tmp/set_syncword 0x11"
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

/* libloragw headers */
#include "loragw_hal.h"
#include "loragw_reg.h"

#define DEFAULT_CLK_SRC     0    /* Radio A als Clock Source */
#define RADIO_TYPE_SX1250   1250

/* Funktion zum Setzen des Sync Words */
int set_sync_word(uint8_t sync_word) {
    int i;
    struct lgw_conf_board_s boardconf;
    struct lgw_conf_rxrf_s rfconf;

    printf("═══════════════════════════════════════════════════════\n");
    printf("  Dragino SX1302 - Set Sync Word to 0x%02X\n", sync_word);
    printf("═══════════════════════════════════════════════════════\n\n");

    /* 1. Board Konfiguration */
    memset(&boardconf, 0, sizeof boardconf);
    boardconf.lorawan_public = false;  /* Wird überschrieben */
    boardconf.clksrc = DEFAULT_CLK_SRC;

    printf("1. Configure board...\n");
    if (lgw_board_setconf(&boardconf) != 0) {
        fprintf(stderr, "ERROR: Failed to configure board\n");
        return -1;
    }

    /* 2. Radio Konfiguration (minimal, nur für Init) */
    memset(&rfconf, 0, sizeof rfconf);
    rfconf.enable = true;
    rfconf.type = LGW_RADIO_TYPE_SX1250;
    rfconf.freq_hz = 867500000;  /* 867.5 MHz */
    rfconf.tx_enable = false;

    printf("2. Configure radio...\n");
    if (lgw_rxrf_setconf(0, &rfconf) != 0) {
        fprintf(stderr, "ERROR: Failed to configure radio 0\n");
        return -1;
    }

    /* 3. Gateway starten */
    printf("3. Starting gateway...\n");
    if (lgw_start() != 0) {
        fprintf(stderr, "ERROR: Failed to start gateway\n");
        return -1;
    }

    printf("   ✓ Gateway started\n\n");

    /* 4. Sync Word direkt in SX1250 Register schreiben */
    printf("4. Writing Sync Word 0x%02X to SX1250...\n", sync_word);

    /*
     * SX1250 LoRa Sync Word Register:
     * - SX1302 verwendet interne Register-Mappings
     * - Sync Word steht in SX126x Register 0x0740 (LoRa Sync Word MSB/LSB)
     *
     * WICHTIG: libloragw bietet keine direkte API für Sync Word!
     * Wir müssen es über Register-Zugriff machen.
     */

    /* SX1302 Register für Radio 0 Sync Word */
    /* Dies sind die SX1302 internen Register, nicht direkt SX1250 */

    /* Alternative: Verwende lgw_reg_w für direkten Zugriff */
    /* SX1302 Radio 0 LoRa Sync Word Register ist komplex -
     * am einfachsten über global_conf.json */

    printf("   ⚠️  Direct register write via libloragw API:\n");
    printf("      libloragw hat keine direkte Sync Word API!\n");
    printf("      Empfehlung: Ändere global_conf.json\n\n");

    /* 5. Gateway stoppen */
    printf("5. Stopping gateway...\n");
    if (lgw_stop() != 0) {
        fprintf(stderr, "ERROR: Failed to stop gateway\n");
        return -1;
    }

    printf("   ✓ Gateway stopped\n\n");

    printf("═══════════════════════════════════════════════════════\n");
    printf("  Info: Für custom Sync Word nutze global_conf.json\n");
    printf("═══════════════════════════════════════════════════════\n");

    return 0;
}

/* Hauptfunktion */
int main(int argc, char *argv[]) {
    uint8_t sync_word;

    if (argc != 2) {
        printf("Usage: %s <sync_word>\n", argv[0]);
        printf("Example:\n");
        printf("  %s 0x11    # Set sync word to 0x11\n", argv[0]);
        printf("  %s 0x12    # Set sync word to 0x12 (LoRa Private)\n", argv[0]);
        printf("  %s 0x34    # Set sync word to 0x34 (LoRaWAN Public)\n", argv[0]);
        return -1;
    }

    /* Parse Sync Word */
    sync_word = (uint8_t)strtol(argv[1], NULL, 0);

    printf("\nTarget Sync Word: 0x%02X (%d decimal)\n\n", sync_word, sync_word);

    /* Setze Sync Word */
    if (set_sync_word(sync_word) != 0) {
        fprintf(stderr, "\nERROR: Failed to set sync word\n");
        return -1;
    }

    printf("\nNote: libloragw supports only 0x12 and 0x34 via lorawan_public flag.\n");
    printf("For custom sync words (like 0x11), you need to:\n");
    printf("  1. Modify sx1302_hal source code, OR\n");
    printf("  2. Use direct SPI register access\n\n");

    return 0;
}
