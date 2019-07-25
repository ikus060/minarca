/**
 * Copyright(C) 2013 Patrik Dufresne Service Logiciel <info@patrikdufresne.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.patrikdufresne.minarca.ui;

import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.widgets.Display;
import org.eclipse.ui.forms.FormColors;

/**
 * This implementation of Form Colors provide more variety of colors and allow to select the base color for the
 * background.
 * 
 * @author Patrik Dufresne
 * 
 */
public class MinarcaFormColors extends FormColors {

    public static String ERROR = "ERROR";

    public static String SUCESS = "SUCESS";

    public static RGB rgb(String color) {
        return new RGB(Integer.valueOf(color.substring(1, 3), 16), Integer.valueOf(color.substring(3, 5), 16), Integer.valueOf(color.substring(5, 7), 16));
    }

    private final boolean widgetColors;

    /**
     * Create Minarca colors.
     * 
     * @param display
     * @param widgetColors
     *            True to use the widget colors.
     */
    public MinarcaFormColors(Display display, boolean widgetColors) {
        super(display);
        this.widgetColors = widgetColors;
        initialize();
    }

    /**
     * Completely replace the initialisation to use either the LIST colors or the DIALOG colors.
     */
    @Override
    protected void initialize() {
        if (widgetColors) {
            background = display.getSystemColor(SWT.COLOR_WIDGET_BACKGROUND);
            foreground = display.getSystemColor(SWT.COLOR_WIDGET_FOREGROUND);
        } else {
            background = display.getSystemColor(SWT.COLOR_LIST_BACKGROUND);
            foreground = display.getSystemColor(SWT.COLOR_LIST_FOREGROUND);
        }
        initializeColorTable();
        updateBorderColor();
    }

    @Override
    protected void initializeColorTable() {
        super.initializeColorTable();
        createColor(ERROR, rgb("#ff0000"));
        createColor(SUCESS, rgb("#3b9444"));
    }

}
