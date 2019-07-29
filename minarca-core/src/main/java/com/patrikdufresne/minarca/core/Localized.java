/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.util.Locale;

import org.slf4j.LoggerFactory;
import org.xnap.commons.i18n.I18n;
import org.xnap.commons.i18n.I18nFactory;

public class Localized {

    private static final String BUNDLE_NAME = "com.patrikdufresne.minarca.core.messages";

    private static I18n i18n;

    static {
        LoggerFactory.getLogger(Localized.class).info("using default locale {}", Locale.getDefault());
        i18n = I18nFactory.getI18n(Localized.class, BUNDLE_NAME, Locale.getDefault(), I18nFactory.FALLBACK);
    }

    /**
     * Localize the given text (a la gettext).
     * 
     * @param text
     * @return
     */
    public static String _(String text) {
        return i18n.tr(text);
    }

    /**
     * Localize the given text (a la gettext). The string may contains <code>{0}</code> as place holder for
     * <code>args</code>.
     * 
     * @param text
     * @param args
     * @return
     */
    public static String _(String text, Object... args) {
        return i18n.tr(text, args);
    }
}
