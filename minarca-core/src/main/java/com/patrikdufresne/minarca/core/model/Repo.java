/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.model;

import java.util.Date;

import com.google.gson.annotations.SerializedName;

public class Repo {

    @SerializedName("display_name")
    public String displayName;
    public String encoding;
    public int keepdays;
    @SerializedName("last_backup_date")
    public Date lastBackupDate;
    public int maxage;
    public String name;
    public RepoStatus status;

}