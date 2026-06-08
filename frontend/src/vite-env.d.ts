// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_BACKEND_PORT: number
    readonly VITE_FOOTER_TEXT: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
