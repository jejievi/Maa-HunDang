package com.aliothmoon.maafw.di

import com.aliothmoon.maafw.update.GitHubReleasesApi
import com.aliothmoon.maafw.update.GitHubUpdateClient
import com.aliothmoon.maafw.update.OkHttpUpdateDownloader
import com.aliothmoon.maafw.update.UpdateService
import org.koin.dsl.module

/**
 * 更新链路只接 GitHub：本项目不出 Mirror酱 包，也不再注册 MirrorChyan 客户端，
 * GitHubUpdateClient 的 mirrorRelease 保持默认的空实现，永远不会去问 Mirror酱
 */
val updateModule = module {
    single { GitHubReleasesApi(get()) }
    single { GitHubUpdateClient(get()) }
    single {
        UpdateService(
            clients = listOf(
                get<GitHubUpdateClient>(),
            ),
        )
    }
    single { OkHttpUpdateDownloader(get()) }
}