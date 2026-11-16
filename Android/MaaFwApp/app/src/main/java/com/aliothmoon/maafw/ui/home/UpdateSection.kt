package com.aliothmoon.maafw.ui.home

import android.content.Intent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.core.net.toUri
import com.aliothmoon.maafw.R
import com.aliothmoon.maafw.i18n.asString
import com.aliothmoon.maafw.settings.SettingsIntent
import com.aliothmoon.maafw.settings.UpdatePanelState
import com.aliothmoon.maafw.theme.MaaDesignTokens
import com.aliothmoon.maafw.theme.MaaIcons
import com.aliothmoon.maafw.theme.MaaTheme
import com.aliothmoon.maafw.theme.OpaqueTheme
import com.aliothmoon.maafw.ui.components.ITextFieldWithFocus
import com.aliothmoon.maafw.ui.components.LocalCardRowBleed
import com.aliothmoon.maafw.ui.components.MaaChoiceChip
import com.aliothmoon.maafw.ui.components.MaaOutlinedButton
import com.aliothmoon.maafw.ui.components.horizontalBleed
import com.aliothmoon.maafw.ui.components.updateSourceLabel
import com.aliothmoon.maafw.update.UpdateChannel
import com.aliothmoon.maafw.update.UpdateSource
import com.aliothmoon.maafw.update.formatSpeed
import timber.log.Timber

/** 概览行左侧标签；不用 MaaFieldLabel（组标题档），颜色跟 MaaInfoRow 的 onSurface 一致 */
@Composable
private fun UpdateRowLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurface,
    )
}

/**
 * 概览卡里的更新区块（无独立卡头）：渠道选择与检查、下载入口都在这；
 * 启动自检与自动下载两个开关留在设置页的更新卡
 */
@Composable
internal fun UpdateSection(
    update: UpdatePanelState,
    onSettingsIntent: (SettingsIntent) -> Unit,
) {
    val settingsEnabled = !update.downloading
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(MaaDesignTokens.Spacing.xs),
    ) {
        UpdateRowLabel(stringResource(R.string.settings_update_channel))
        Spacer(Modifier.weight(1f))
        listOf(
            UpdateChannel.STABLE to stringResource(R.string.settings_update_channel_stable),
            UpdateChannel.BETA to stringResource(R.string.settings_update_channel_beta),
        ).forEach { (channel, label) ->
            MaaChoiceChip(
                label = label,
                selected = update.channel == channel,
                enabled = settingsEnabled,
                role = Role.RadioButton,
                onClick = { onSettingsIntent(SettingsIntent.SetUpdateChannel(channel)) },
            )
        }
    }
    UpdateStatus(update)
    if (update.downloading) {
        DownloadProgressRow(update, onSettingsIntent)
    } else {
        MaaOutlinedButton(
            onClick = { onSettingsIntent(SettingsIntent.CheckUpdate) },
            enabled = !update.checking,
            modifier = Modifier.fillMaxWidth(),
            // 描边款 + 主色内容；整块填充在概览卡里太重
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = MaterialTheme.colorScheme.primary,
            ),
        ) {
            // 检查中图标位换转圈；颜色跟 LocalContentColor 才能吃到禁用态透明度
            // （strokeWidth 与 HomeScreen 的行内转圈同档）
            if (update.checking) {
                CircularProgressIndicator(
                    modifier = Modifier.size(MaaDesignTokens.IconSize.md),
                    strokeWidth = MaaDesignTokens.Border.marker,
                    color = LocalContentColor.current,
                )
            } else {
                Icon(
                    imageVector = Icons.Outlined.Refresh,
                    contentDescription = null,
                    modifier = Modifier.size(MaaDesignTokens.IconSize.md),
                )
            }
            Spacer(Modifier.width(MaaDesignTokens.Spacing.sm))
            Text(
                text = stringResource(
                    if (update.checking) R.string.settings_update_checking
                    else R.string.settings_update_check,
                ),
            )
        }
    }
}

@Composable
private fun DownloadProgressRow(
    update: UpdatePanelState,
    onSettingsIntent: (SettingsIntent) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(MaaDesignTokens.Spacing.sm),
    ) {
        if (update.totalBytes > 0) {
            LinearProgressIndicator(
                progress = { update.downloadedBytes.toFloat() / update.totalBytes },
                modifier = Modifier.weight(1f),
            )
            Text(
                text = "${update.downloadedBytes.coerceAtLeast(0L) * 100 / update.totalBytes}%",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            // 总长未知：不确定进度条，没有可算的百分比
            LinearProgressIndicator(modifier = Modifier.weight(1f))
        }
        if (update.bytesPerSecond >= 0) {
            Text(
                text = formatSpeed(update.bytesPerSecond),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        IconButton(
            onClick = { onSettingsIntent(SettingsIntent.CancelDownload) },
            modifier = Modifier.size(MaaDesignTokens.IconContainer.sm),
        ) {
            Icon(
                imageVector = Icons.Outlined.Close,
                contentDescription = stringResource(R.string.settings_update_cancel_download),
                modifier = Modifier.size(MaaDesignTokens.IconSize.sm),
            )
        }
    }
}

@Composable
private fun UpdateStatus(update: UpdatePanelState) {
    // 检查结果不在这里出：新版本与失败走弹窗，已是最新走 Toast（SettingsEffect.ShowMessage）
    update.errorMessage?.let {
        Text(
            text = it.asString(),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.error,
        )
    }
}
