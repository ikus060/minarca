/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.model;

import java.util.List;
import java.util.stream.Collectors;

import com.google.gson.annotations.SerializedName;

/**
 * 
 * @author Patrik Dufresne
 * 
 */
public class CurrentUser {

    public String email;
    @SerializedName("is_admin")
    public boolean isAdmin;
    public List<Repo> repos;
    public String username;
    @SerializedName("user_root")
    public String userRoot;

    /**
     * Return list of repository matching the given repo name. This return sub repository name like computername/C,
     * computername/D
     * 
     * @param repositoryName
     * @return
     */
    public List<Repo> findRepos(final String repositoryName) {
        return repos.stream().filter(r -> r.name.equals(repositoryName) || r.name.startsWith(repositoryName + "/")).collect(Collectors.toList());
    }
}
