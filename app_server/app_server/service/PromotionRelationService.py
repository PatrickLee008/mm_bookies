"""
推广关系服务
处理推广关系的创建、更新和查询
"""
import datetime
from decimal import Decimal
from app_server import db, app
from app_server.model.MAppPromotionRelationModel import MAppPromotionRelation, RelationStatus
from app_server.model.AppMemberModel import AppMember
from app_server.model.MAppInvitationActivityModel import MAppInvitationActivity
from app_server.utils.Kits import Kits


class PromotionRelationService:
    """推广关系服务类"""

    @staticmethod
    def check_invitation_limit(promoter_id, activity_id=None):
        """
        检查推广人是否已达到邀请人数上限

        Args:
            promoter_id: 推广人ID
            activity_id: 活动ID（可选，如果提供则检查特定活动的限制）

        Returns:
            (bool, str, dict): (是否可以邀请, 错误信息, 邀请统计信息)
        """
        try:
            # 如果提供了活动ID，检查活动的邀请限制
            if activity_id:
                activity = MAppInvitationActivity.query.filter_by(
                    id=activity_id,
                    del_flag=0
                ).first()

                if not activity:
                    return False, "Activity not found", {}

                # 如果活动设置了邀请限制（max_invitations_per_user > 0）
                max_invitations = activity.max_invitations_per_user if hasattr(activity, 'max_invitations_per_user') else 0

                if max_invitations and max_invitations > 0:
                    # 统计推广人在该活动时间范围内已邀请的人数（只统计计入活动统计的）
                    invited_count = MAppPromotionRelation.query.join(
                        AppMember, MAppPromotionRelation.invitee_id == AppMember.id
                    ).filter(
                        MAppPromotionRelation.promoter_id == promoter_id,
                        MAppPromotionRelation.status == RelationStatus.ACTIVE.value,
                        MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
                        MAppPromotionRelation.del_flag == 0,
                        AppMember.create_time >= activity.start_date,
                        AppMember.create_time <= activity.end_date
                    ).count()

                    stats = {
                        'current_invitations': invited_count,
                        'max_invitations': max_invitations,
                        'remaining_invitations': max(0, max_invitations - invited_count)
                    }

                    # 检查是否超过限制
                    if invited_count >= max_invitations:
                        return False, f"Invitation limit reached. You can invite up to {max_invitations} people for this activity.", stats

                    return True, "", stats
                else:
                    # 没有限制（但仍然只统计计入活动统计的）
                    invited_count = MAppPromotionRelation.query.join(
                        AppMember, MAppPromotionRelation.invitee_id == AppMember.id
                    ).filter(
                        MAppPromotionRelation.promoter_id == promoter_id,
                        MAppPromotionRelation.status == RelationStatus.ACTIVE.value,
                        MAppPromotionRelation.is_counted_in_activity == True,  # 只统计计入活动的
                        MAppPromotionRelation.del_flag == 0,
                        AppMember.create_time >= activity.start_date,
                        AppMember.create_time <= activity.end_date
                    ).count()

                    stats = {
                        'current_invitations': invited_count,
                        'max_invitations': 0,
                        'remaining_invitations': -1  # -1 表示无限制
                    }
                    return True, "", stats
            else:
                # 没有指定活动，统计总邀请数
                total_invited = MAppPromotionRelation.query.filter_by(
                    promoter_id=promoter_id,
                    status=RelationStatus.ACTIVE.value,
                    del_flag=0
                ).count()

                stats = {
                    'current_invitations': total_invited,
                    'max_invitations': 0,
                    'remaining_invitations': -1
                }
                return True, "", stats

        except Exception as e:
            app.logger.error(f"检查邀请限制失败: {str(e)}")
            return False, f"Failed to check invitation limit: {str(e)}", {}

    @staticmethod
    def check_ip_device_limits(activity_id, invite_ip, invite_device):
        """
        检查IP和设备限制
        
        Args:
            activity_id: 活动ID
            invite_ip: 邀请IP地址
            invite_device: 邀请设备信息
            
        Returns:
            (bool, str): (是否通过检查, 错误信息)
        """
        try:
            activity = MAppInvitationActivity.query.filter_by(
                id=activity_id,
                del_flag=0
            ).first()
            
            if not activity:
                return True, ""  # 活动不存在，不限制
            
            # 获取限制配置
            ip_limit = activity.ip_limit_count if hasattr(activity, 'ip_limit_count') else 0
            imei_limit = activity.imei_limit_count if hasattr(activity, 'imei_limit_count') else 0
            
            # 检查IP限制
            if ip_limit > 0 and invite_ip:
                ip_count = MAppPromotionRelation.query.filter(
                    MAppPromotionRelation.activity_id == activity_id,
                    MAppPromotionRelation.invite_ip == invite_ip,
                    MAppPromotionRelation.status == RelationStatus.ACTIVE.value,
                    MAppPromotionRelation.del_flag == 0
                ).count()
                
                if ip_count >= ip_limit:
                    return False, f"Registration limit reached: Only one registration is allowed per IP address."
            
            # 检查设备限制
            if imei_limit > 0 and invite_device:
                device_count = MAppPromotionRelation.query.filter(
                    MAppPromotionRelation.activity_id == activity_id,
                    MAppPromotionRelation.invite_device == invite_device,
                    MAppPromotionRelation.status == RelationStatus.ACTIVE.value,
                    MAppPromotionRelation.del_flag == 0
                ).count()
                
                if device_count >= imei_limit:
                    return False, f"Registration limit reached: Only one registration is allowed per IP address."

            return True, ""
            
        except Exception as e:
            app.logger.error(f"检查IP/设备限制失败: {str(e)}")
            return True, ""  # 出错时不限制，避免影响正常注册

    @staticmethod
    def create_promotion_relation(
            promoter_id,
            invitee_id,
            invite_code,
            activity_id=None,
            invite_channel='APP',
            invite_ip=None,
            invite_device=None,
            tenant_id=None,
            aid=None
    ):
        """
        创建推广关系

        Args:
            promoter_id: 推广人ID
            invitee_id: 被邀请人ID
            invite_code: 邀请码
            activity_id: 活动ID（可选）
            invite_channel: 邀请渠道（默认APP）
            invite_ip: 邀请IP地址
            invite_device: 邀请设备信息
            tenant_id: 租户ID
            aid: 代理ID

        Returns:
            推广关系对象，如果失败返回None
        """
        try:
            # 检查是否已存在推广关系
            existing_relation = MAppPromotionRelation.query.filter_by(
                invitee_id=invitee_id,
                del_flag=0
            ).first()

            if existing_relation:
                app.logger.warning(f"被邀请人已存在推广关系: invitee_id={invitee_id}, promoter={existing_relation.promoter_id}")
                return existing_relation

            # 检查邀请人数限制（如果提供了活动ID）
            # 注意：即使超出限制，仍然创建推广关系，只是标记为不计入活动奖励
            is_counted_in_activity = True  # 默认计入
            activity = None
            if activity_id:
                activity = MAppInvitationActivity.query.filter_by(id=activity_id, del_flag=0).first()
                can_invite, error_msg, stats = PromotionRelationService.check_invitation_limit(promoter_id, activity_id)
                if not can_invite:
                    is_counted_in_activity = False  # 超出限制，标记为不计入奖励
                    app.logger.info(
                        f"邀请人数已达活动上限，创建关系但不计入奖励: promoter_id={promoter_id}, activity_id={activity_id}, "
                        f"current={stats.get('current_invitations', 0)}, max={stats.get('max_invitations', 0)}"
                    )
                    
                    # 发送消息提醒邀请者
                    try:
                        from app_server.utils.MemberMessageService import MemberMessageService
                        
                        activity_name = activity.title if activity else "Invitation Activity"
                        max_invites = stats.get('max_invitations', 0)
                        
                        title = "Invitation Limit Reached"
                        content = (
                            f"Congratulations! You have reached the maximum invitation limit ({max_invites} people) "
                            f"for the activity '{activity_name}'. "
                            f"New invitees will still be registered but will not count towards your rewards."
                        )
                        
                        MemberMessageService.send_to_member(
                            member_id=promoter_id,
                            title=title,
                            content=content,
                            message_type='PROMOTION',
                            source='SYSTEM',
                            business_id=activity_id,
                            target_url='/bonus/activity/record',
                            target_type='PAGE',
                            aid=aid
                        )
                        app.logger.info(f"邀请上限提醒消息已发送: promoter_id={promoter_id}, activity_id={activity_id}")
                    except Exception as msg_ex:
                        app.logger.warning(f"发送邀请上限提醒消息失败: {str(msg_ex)}")
                        # 消息发送失败不影响主流程
                
            # 获取推广人和被邀请人信息
            promoter = AppMember.query.filter_by(id=promoter_id, del_flag=0).first()
            invitee = AppMember.query.filter_by(id=invitee_id, del_flag=0).first()

            if not promoter or not invitee:
                app.logger.error(f"推广人或被邀请人不存在: promoter_id={promoter_id}, invitee_id={invitee_id}")
                return None

            # 创建推广关系
            promotion_relation = MAppPromotionRelation(
                id=Kits.generate_uuid(),
                activity_id=activity_id,
                promoter_id=promoter_id,
                promoter_username=promoter.username,
                invitee_id=invitee_id,
                invitee_username=invitee.username,
                relation_level=1,  # 一级关系
                invite_code=invite_code,
                invite_channel=invite_channel,
                invite_time=datetime.datetime.now(),
                register_time=datetime.datetime.now(),
                invite_ip=invite_ip,
                invite_device=invite_device,
                status=RelationStatus.ACTIVE.value,
                is_counted_in_activity=is_counted_in_activity,  # 根据邀请限制设置是否计入奖励
                is_effective=False,
                total_deposit=Decimal('0.00'),
                total_bet=Decimal('0.00'),
                total_commission=Decimal('0.00'),
                first_deposit_amount=Decimal('0.00'),
                aid=aid or invitee.aid,
                tenant_id=tenant_id or invitee.tenant_id,
                create_time=datetime.datetime.now(),
                update_time=datetime.datetime.now(),
                del_flag=0
            )

            db.session.add(promotion_relation)
            db.session.commit()

            app.logger.info(
                f"创建推广关系成功: id={promotion_relation.id}, "
                f"promoter={promoter_id}, invitee={invitee_id}, code={invite_code}"
            )

            return promotion_relation

        except Exception as e:
            app.logger.error(f"创建推广关系失败: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def update_first_deposit(invitee_id, deposit_amount):
        """
        更新被邀请人首次存款信息

        Args:
            invitee_id: 被邀请人ID
            deposit_amount: 存款金额

        Returns:
            是否成功
        """
        try:
            relation = MAppPromotionRelation.query.filter_by(
                invitee_id=invitee_id,
                status=RelationStatus.ACTIVE.value,
                del_flag=0
            ).first()

            if not relation:
                app.logger.warning(f"未找到推广关系: invitee_id={invitee_id}")
                return False

            # 如果还没有首次存款记录，则更新
            if not relation.first_deposit_time:
                relation.first_deposit_time = datetime.datetime.now()
                relation.first_deposit_amount = Decimal(str(deposit_amount))
                relation.update_time = datetime.datetime.now()

                db.session.commit()

                app.logger.info(
                    f"更新首次存款成功: invitee_id={invitee_id}, "
                    f"amount={deposit_amount}"
                )

            return True

        except Exception as e:
            app.logger.error(f"更新首次存款失败: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def update_statistics(
            invitee_id,
            deposit_amount=None,
            bet_amount=None,
            commission_amount=None
    ):
        """
        更新推广关系的统计数据

        Args:
            invitee_id: 被邀请人ID
            deposit_amount: 存款金额增量（可选）
            bet_amount: 投注金额增量（可选）
            commission_amount: 佣金金额增量（可选）

        Returns:
            是否成功
        """
        try:
            relation = MAppPromotionRelation.query.filter_by(
                invitee_id=invitee_id,
                status=RelationStatus.ACTIVE.value,
                del_flag=0
            ).first()

            if not relation:
                app.logger.warning(f"未找到推广关系: invitee_id={invitee_id}")
                return False

            # 更新统计数据
            if deposit_amount is not None and deposit_amount > 0:
                relation.total_deposit += Decimal(str(deposit_amount))

            if bet_amount is not None and bet_amount > 0:
                relation.total_bet += Decimal(str(bet_amount))

            if commission_amount is not None and commission_amount > 0:
                relation.total_commission += Decimal(str(commission_amount))

            # 检查是否达到有效会员条件
            # 条件：累计存款 >= 100 且累计投注 >= 1000
            if not relation.is_effective:
                if (relation.total_deposit >= Decimal('100') and
                        relation.total_bet >= Decimal('1000')):
                    relation.is_effective = True
                    relation.effective_time = datetime.datetime.now()
                    app.logger.info(f"用户成为有效会员: invitee_id={invitee_id}")

            relation.update_time = datetime.datetime.now()
            db.session.commit()

            app.logger.info(
                f"更新推广关系统计成功: invitee_id={invitee_id}, "
                f"deposit={deposit_amount}, bet={bet_amount}, commission={commission_amount}"
            )

            return True

        except Exception as e:
            app.logger.error(f"更新推广关系统计失败: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def get_promoter_by_invitee(invitee_id):
        """
        根据被邀请人ID查询推广人

        Args:
            invitee_id: 被邀请人ID

        Returns:
            推广关系对象，如果不存在返回None
        """
        return MAppPromotionRelation.query.filter_by(
            invitee_id=invitee_id,
            relation_level=1,
            del_flag=0
        ).first()

    @staticmethod
    def get_invitees_by_promoter(promoter_id, relation_level=1, is_effective=None):
        """
        根据推广人ID查询邀请列表

        Args:
            promoter_id: 推广人ID
            relation_level: 关系层级（默认1）
            is_effective: 是否只查有效会员（可选）

        Returns:
            推广关系列表
        """
        query = MAppPromotionRelation.query.filter_by(
            promoter_id=promoter_id,
            relation_level=relation_level,
            status=RelationStatus.ACTIVE.value,
            del_flag=0
        )

        if is_effective is not None:
            query = query.filter_by(is_effective=is_effective)

        return query.order_by(MAppPromotionRelation.invite_time.desc()).all()

    @staticmethod
    def count_invitees(promoter_id, is_effective=None):
        """
        统计推广人的邀请数量

        Args:
            promoter_id: 推广人ID
            is_effective: 是否只统计有效会员（可选）

        Returns:
            邀请数量
        """
        query = MAppPromotionRelation.query.filter_by(
            promoter_id=promoter_id,
            status=RelationStatus.ACTIVE.value,
            del_flag=0
        )

        if is_effective is not None:
            query = query.filter_by(is_effective=is_effective)

        return query.count()

    @staticmethod
    def invalidate_relation(relation_id, reason):
        """
        失效推广关系

        Args:
            relation_id: 推广关系ID
            reason: 失效原因

        Returns:
            是否成功
        """
        try:
            relation = MAppPromotionRelation.query.filter_by(
                id=relation_id,
                del_flag=0
            ).first()

            if not relation:
                app.logger.warning(f"未找到推广关系: relation_id={relation_id}")
                return False

            relation.status = RelationStatus.INVALID.value
            relation.invalid_reason = reason
            relation.invalid_time = datetime.datetime.now()
            relation.update_time = datetime.datetime.now()

            db.session.commit()

            app.logger.info(
                f"失效推广关系成功: relation_id={relation_id}, reason={reason}"
            )

            return True

        except Exception as e:
            app.logger.error(f"失效推广关系失败: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def get_promotion_statistics(promoter_id):
        """
        获取推广人的统计信息

        Args:
            promoter_id: 推广人ID

        Returns:
            统计信息字典
        """
        try:
            # 查询所有邀请关系
            relations = MAppPromotionRelation.query.filter_by(
                promoter_id=promoter_id,
                status=RelationStatus.ACTIVE.value,
                del_flag=0
            ).all()

            # 统计数据
            total_invitees = len(relations)
            effective_invitees = sum(1 for r in relations if r.is_effective)
            total_deposit = sum(r.total_deposit for r in relations)
            total_bet = sum(r.total_bet for r in relations)
            total_commission = sum(r.total_commission for r in relations)

            return {
                'total_invitees': total_invitees,
                'effective_invitees': effective_invitees,
                'total_deposit': float(total_deposit),
                'total_bet': float(total_bet),
                'total_commission': float(total_commission),
                'effective_rate': (effective_invitees / total_invitees * 100) if total_invitees > 0 else 0
            }

        except Exception as e:
            app.logger.error(f"获取推广统计失败: {str(e)}")
            return {
                'total_invitees': 0,
                'effective_invitees': 0,
                'total_deposit': 0.0,
                'total_bet': 0.0,
                'total_commission': 0.0,
                'effective_rate': 0.0
            }
