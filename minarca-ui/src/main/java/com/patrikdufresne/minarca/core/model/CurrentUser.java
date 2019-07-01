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
