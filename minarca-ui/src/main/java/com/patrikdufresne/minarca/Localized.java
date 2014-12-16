/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca;

import java.util.Locale;

import org.slf4j.LoggerFactory;
import org.xnap.commons.i18n.I18n;
import org.xnap.commons.i18n.I18nFactory;

public class Localized {

    private static final String BUNDLE_NAME = "com.patrikdufresne.minarca.messages";

    private static I18n i18n;

    static {
        LoggerFactory.getLogger(Localized.class).info("using default locale {}", Locale.getDefault());
        i18n = I18nFactory.getI18n(Localized.class, BUNDLE_NAME, Locale.getDefault(), I18nFactory.DEFAULT);
    }

    public static String _(String text) {
        return i18n.tr(text);
    }

    public static String _(String text, Object... args) {
        return i18n.tr(text, args);
    }
}
