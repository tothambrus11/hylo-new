
tc-bench.real:     file format elf64-x86-64


Disassembly of section .text:

000000000038dc70 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF>:
  38dc70:	push   %rbp
  38dc71:	mov    %rsp,%rbp
  38dc74:	push   %r15
  38dc76:	push   %r14
  38dc78:	push   %r13
  38dc7a:	push   %r12
  38dc7c:	push   %rbx
  38dc7d:	sub    $0x128,%rsp
  38dc84:	mov    %r9,%r14
  38dc87:	mov    %r8,-0x48(%rbp)
  38dc8b:	mov    %rcx,-0x40(%rbp)
  38dc8f:	mov    %rdx,-0x38(%rbp)
  38dc93:	mov    %rsi,%rbx
  38dc96:	mov    0x18(%rbp),%r13
  38dc9a:	lea    -0x118(%rbp),%r15
  38dca1:	mov    %r15,%rax
  38dca4:	mov    %r9,%rsi
  38dca7:	mov    %r13,%rcx
  38dcaa:	call   3889e0 <$s8FrontEnd9TypeStoreVyAA0C4Tree_pAA03AnyC8IdentityVcig>
  38dcaf:	lea    -0xb8(%rbp),%r12
  38dcb6:	mov    %r12,%rax
  38dcb9:	mov    %rbx,%rdi
  38dcbc:	mov    %r14,%rsi
  38dcbf:	mov    %r13,%rcx
  38dcc2:	call   3889e0 <$s8FrontEnd9TypeStoreVyAA0C4Tree_pAA03AnyC8IdentityVcig>
  38dcc7:	mov    -0x100(%rbp),%rbx
  38dcce:	mov    %r15,%rdi
  38dcd1:	mov    %rbx,%rsi
  38dcd4:	call   101590 <__swift_project_boxed_opaque_existential_1>
  38dcd9:	mov    %rax,%rdi
  38dcdc:	mov    %rbx,%rsi
  38dcdf:	mov    $0x1,%edx
  38dce4:	call   74830 <swift_getDynamicType@plt>
  38dce9:	mov    %rax,%rbx
  38dcec:	mov    -0xa0(%rbp),%r15
  38dcf3:	mov    %r12,%rdi
  38dcf6:	mov    %r15,%rsi
  38dcf9:	call   101590 <__swift_project_boxed_opaque_existential_1>
  38dcfe:	mov    %rax,%rdi
  38dd01:	mov    %r15,%rsi
  38dd04:	mov    $0x1,%edx
  38dd09:	call   74830 <swift_getDynamicType@plt>
  38dd0e:	cmp    %rax,%rbx
  38dd11:	je     38dd32 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xc2>
  38dd13:	lea    -0xb8(%rbp),%rdi
  38dd1a:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38dd1f:	lea    -0x118(%rbp),%rdi
  38dd26:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38dd2b:	xor    %ebx,%ebx
  38dd2d:	jmp    38e3b4 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x744>
  38dd32:	lea    -0x118(%rbp),%rdi
  38dd39:	lea    -0xe8(%rbp),%r15
  38dd40:	mov    %r15,%rsi
  38dd43:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38dd48:	lea    0x317d71(%rip),%rdi        # 6a5ac0 <$s8FrontEnd8TypeTree_pMD>
  38dd4f:	call   8da10 <__swift_instantiateConcreteTypeFromMangledName>
  38dd54:	mov    %rax,%rbx
  38dd57:	lea    0x30b312(%rip),%rcx        # 699070 <$s8FrontEnd15TypeApplicationVN>
  38dd5e:	lea    -0x90(%rbp),%rdi
  38dd65:	mov    %r15,%rsi
  38dd68:	mov    %rax,%rdx
  38dd6b:	xor    %r8d,%r8d
  38dd6e:	call   73930 <swift_dynamicCast@plt>
  38dd73:	test   %al,%al
  38dd75:	je     38de9d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x22d>
  38dd7b:	mov    -0x90(%rbp),%r13
  38dd82:	mov    -0x88(%rbp),%rax
  38dd89:	mov    %rax,-0x30(%rbp)
  38dd8d:	mov    -0x80(%rbp),%rax
  38dd91:	mov    %rax,-0xf0(%rbp)
  38dd98:	mov    -0x78(%rbp),%r12
  38dd9c:	lea    -0xb8(%rbp),%rdi
  38dda3:	lea    -0x148(%rbp),%r15
  38ddaa:	mov    %r15,%rsi
  38ddad:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38ddb2:	lea    0x30b2b7(%rip),%rcx        # 699070 <$s8FrontEnd15TypeApplicationVN>
  38ddb9:	lea    -0x70(%rbp),%rdi
  38ddbd:	mov    $0x7,%r8d
  38ddc3:	mov    %r15,%rsi
  38ddc6:	mov    %rbx,%rdx
  38ddc9:	call   73930 <swift_dynamicCast@plt>
  38ddce:	mov    -0x70(%rbp),%rsi
  38ddd2:	mov    -0x68(%rbp),%rax
  38ddd6:	mov    %rax,-0x50(%rbp)
  38ddda:	mov    -0x60(%rbp),%r15
  38ddde:	mov    -0x58(%rbp),%rbx
  38dde2:	mov    %r13,%rdi
  38dde5:	mov    -0x38(%rbp),%rdx
  38dde9:	mov    -0x40(%rbp),%rcx
  38dded:	mov    -0x48(%rbp),%r8
  38ddf1:	mov    %r14,%r9
  38ddf4:	push   0x18(%rbp)
  38ddf7:	push   0x10(%rbp)
  38ddfa:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38ddff:	add    $0x10,%rsp
  38de03:	test   $0x1,%al
  38de05:	je     38df6b <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x2fb>
  38de0b:	mov    %r15,-0x120(%rbp)
  38de12:	mov    0x10(%r12),%r13
  38de17:	xor    %r15d,%r15d
  38de1a:	nopw   0x0(%rax,%rax,1)
  38de20:	cmp    %r15,%r13
  38de23:	je     38e17d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x50d>
  38de29:	cmp    0x10(%r12),%r15
  38de2e:	jae    38e6fe <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa8e>
  38de34:	cmp    0x10(%rbx),%r15
  38de38:	je     38de6f <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x1ff>
  38de3a:	jae    38e700 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa90>
  38de40:	mov    0x20(%r12,%r15,8),%rdi
  38de45:	mov    0x20(%rbx,%r15,8),%rsi
  38de4a:	mov    -0x38(%rbp),%rdx
  38de4e:	mov    -0x40(%rbp),%rcx
  38de52:	mov    -0x48(%rbp),%r8
  38de56:	mov    %r14,%r9
  38de59:	push   0x18(%rbp)
  38de5c:	push   0x10(%rbp)
  38de5f:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38de64:	add    $0x10,%rsp
  38de68:	inc    %r15
  38de6b:	test   $0x1,%al
  38de6d:	jne    38de20 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x1b0>
  38de6f:	mov    -0x120(%rbp),%rdi
  38de76:	call   73320 <swift_release@plt>
  38de7b:	mov    -0x50(%rbp),%rdi
  38de7f:	call   73320 <swift_release@plt>
  38de84:	mov    %r12,%rdi
  38de87:	call   73320 <swift_release@plt>
  38de8c:	mov    -0xf0(%rbp),%rdi
  38de93:	call   73320 <swift_release@plt>
  38de98:	jmp    38df93 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x323>
  38de9d:	lea    0x2f84e4(%rip),%rcx        # 686388 <$s8FrontEnd5ArrowVN>
  38dea4:	lea    -0x90(%rbp),%rdi
  38deab:	lea    -0xe8(%rbp),%rsi
  38deb2:	mov    %rbx,%rdx
  38deb5:	xor    %r8d,%r8d
  38deb8:	call   73930 <swift_dynamicCast@plt>
  38debd:	test   %al,%al
  38debf:	mov    %r14,-0xc0(%rbp)
  38dec6:	je     38dfc3 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x353>
  38decc:	mov    -0x88(%rbp),%rax
  38ded3:	mov    %rax,-0x30(%rbp)
  38ded7:	mov    -0x80(%rbp),%r12
  38dedb:	mov    -0x78(%rbp),%r13
  38dedf:	mov    -0x90(%rbp),%r14d
  38dee6:	lea    -0xb8(%rbp),%rdi
  38deed:	lea    -0x148(%rbp),%r15
  38def4:	mov    %r15,%rsi
  38def7:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38defc:	lea    0x2f8485(%rip),%rcx        # 686388 <$s8FrontEnd5ArrowVN>
  38df03:	lea    -0x70(%rbp),%rdi
  38df07:	mov    $0x7,%r8d
  38df0d:	mov    %r15,%rsi
  38df10:	mov    %rbx,%rdx
  38df13:	call   73930 <swift_dynamicCast@plt>
  38df18:	mov    -0x68(%rbp),%r9
  38df1c:	mov    -0x60(%rbp),%r15
  38df20:	mov    -0x70(%rbp),%r8d
  38df24:	mov    %r14d,%edi
  38df27:	mov    -0x30(%rbp),%rsi
  38df2b:	mov    %r12,%rdx
  38df2e:	mov    %r13,%rcx
  38df31:	push   0x18(%rbp)
  38df34:	push   0x10(%rbp)
  38df37:	push   -0xc0(%rbp)
  38df3d:	push   -0x48(%rbp)
  38df40:	push   -0x40(%rbp)
  38df43:	push   -0x38(%rbp)
  38df46:	push   -0x58(%rbp)
  38df49:	push   %r15
  38df4b:	call   38ef40 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF>
  38df50:	add    $0x40,%rsp
  38df54:	mov    %eax,%ebx
  38df56:	mov    %r12,%rdi
  38df59:	call   73320 <swift_release@plt>
  38df5e:	mov    %r15,%rdi
  38df61:	call   73320 <swift_release@plt>
  38df66:	jmp    38e390 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x720>
  38df6b:	mov    %r12,%rdi
  38df6e:	call   73320 <swift_release@plt>
  38df73:	mov    -0xf0(%rbp),%rdi
  38df7a:	call   73320 <swift_release@plt>
  38df7f:	mov    %rbx,%rdi
  38df82:	call   73320 <swift_release@plt>
  38df87:	mov    %r15,%rdi
  38df8a:	call   73320 <swift_release@plt>
  38df8f:	mov    -0x50(%rbp),%rbx
  38df93:	mov    %rbx,%rdi
  38df96:	call   73320 <swift_release@plt>
  38df9b:	mov    -0x30(%rbp),%rdi
  38df9f:	call   73320 <swift_release@plt>
  38dfa4:	lea    -0xb8(%rbp),%rdi
  38dfab:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38dfb0:	lea    -0x118(%rbp),%rdi
  38dfb7:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38dfbc:	xor    %ebx,%ebx
  38dfbe:	jmp    38e3a8 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x738>
  38dfc3:	lea    0x30a71e(%rip),%rcx        # 6986e8 <$s8FrontEnd5TupleON>
  38dfca:	lea    -0x90(%rbp),%rdi
  38dfd1:	lea    -0xe8(%rbp),%rsi
  38dfd8:	mov    %rbx,%rdx
  38dfdb:	xor    %r8d,%r8d
  38dfde:	call   73930 <swift_dynamicCast@plt>
  38dfe3:	test   %al,%al
  38dfe5:	je     38e0b2 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x442>
  38dfeb:	mov    -0x90(%rbp),%r12
  38dff2:	mov    -0x88(%rbp),%r15
  38dff9:	movzbl -0x80(%rbp),%r13d
  38dffe:	lea    -0xb8(%rbp),%rdi
  38e005:	mov    %rbx,%r14
  38e008:	lea    -0x148(%rbp),%rbx
  38e00f:	mov    %rbx,%rsi
  38e012:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e017:	lea    0x30a6ca(%rip),%rcx        # 6986e8 <$s8FrontEnd5TupleON>
  38e01e:	lea    -0x70(%rbp),%rdi
  38e022:	mov    $0x7,%r8d
  38e028:	mov    %rbx,%rsi
  38e02b:	mov    %r14,%rdx
  38e02e:	call   73930 <swift_dynamicCast@plt>
  38e033:	xor    %ebx,%ebx
  38e035:	cmp    $0x1,%r13b
  38e039:	je     38e390 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x720>
  38e03f:	cmpb   $0x1,-0x60(%rbp)
  38e043:	je     38e390 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x720>
  38e049:	mov    %r15,-0x30(%rbp)
  38e04d:	mov    -0x68(%rbp),%rax
  38e051:	mov    %rax,-0x50(%rbp)
  38e055:	mov    -0x70(%rbp),%rsi
  38e059:	mov    %r12,%rdi
  38e05c:	mov    -0x38(%rbp),%rbx
  38e060:	mov    %rbx,%rdx
  38e063:	mov    -0x40(%rbp),%r15
  38e067:	mov    %r15,%rcx
  38e06a:	mov    -0xc0(%rbp),%r13
  38e071:	mov    -0x48(%rbp),%r14
  38e075:	mov    %r14,%r8
  38e078:	mov    %r13,%r9
  38e07b:	mov    0x18(%rbp),%r12
  38e07f:	push   %r12
  38e081:	mov    0x10(%rbp),%rax
  38e085:	push   %rax
  38e086:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e08b:	add    $0x10,%rsp
  38e08f:	test   $0x1,%al
  38e091:	je     38e37a <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x70a>
  38e097:	mov    -0x30(%rbp),%rdi
  38e09b:	mov    -0x50(%rbp),%rsi
  38e09f:	mov    %rbx,%rdx
  38e0a2:	mov    %r15,%rcx
  38e0a5:	mov    %r14,%r8
  38e0a8:	mov    %r13,%r9
  38e0ab:	push   %r12
  38e0ad:	jmp    38e36a <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x6fa>
  38e0b2:	lea    0x2fc1b7(%rip),%rcx        # 68a270 <$s8FrontEnd15EqualityWitnessVN>
  38e0b9:	lea    -0x90(%rbp),%rdi
  38e0c0:	lea    -0xe8(%rbp),%rsi
  38e0c7:	mov    %rbx,%rdx
  38e0ca:	xor    %r8d,%r8d
  38e0cd:	call   73930 <swift_dynamicCast@plt>
  38e0d2:	test   %al,%al
  38e0d4:	je     38e1e6 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x576>
  38e0da:	mov    -0x90(%rbp),%r12
  38e0e1:	mov    -0x88(%rbp),%rax
  38e0e8:	mov    %rax,-0x30(%rbp)
  38e0ec:	lea    -0xb8(%rbp),%rdi
  38e0f3:	mov    %rbx,%r14
  38e0f6:	lea    -0x148(%rbp),%rbx
  38e0fd:	mov    %rbx,%rsi
  38e100:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e105:	lea    0x2fc164(%rip),%rcx        # 68a270 <$s8FrontEnd15EqualityWitnessVN>
  38e10c:	lea    -0x70(%rbp),%rdi
  38e110:	mov    $0x7,%r8d
  38e116:	mov    %rbx,%rsi
  38e119:	mov    %r14,%rdx
  38e11c:	call   73930 <swift_dynamicCast@plt>
  38e121:	mov    -0x70(%rbp),%rsi
  38e125:	mov    -0x68(%rbp),%rbx
  38e129:	mov    %r12,%rdi
  38e12c:	mov    %r13,%rax
  38e12f:	mov    -0x38(%rbp),%r15
  38e133:	mov    %r15,%rdx
  38e136:	mov    -0x40(%rbp),%r13
  38e13a:	mov    %r13,%rcx
  38e13d:	mov    -0xc0(%rbp),%r12
  38e144:	mov    -0x48(%rbp),%r14
  38e148:	mov    %r14,%r8
  38e14b:	mov    %r12,%r9
  38e14e:	push   %rax
  38e14f:	mov    0x10(%rbp),%rax
  38e153:	push   %rax
  38e154:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e159:	add    $0x10,%rsp
  38e15d:	test   $0x1,%al
  38e15f:	je     38e37a <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x70a>
  38e165:	mov    -0x30(%rbp),%rdi
  38e169:	mov    %rbx,%rsi
  38e16c:	mov    %r15,%rdx
  38e16f:	mov    %r13,%rcx
  38e172:	mov    %r14,%r8
  38e175:	mov    %r12,%r9
  38e178:	jmp    38e367 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x6f7>
  38e17d:	mov    %r12,%rdi
  38e180:	call   73320 <swift_release@plt>
  38e185:	mov    -0xf0(%rbp),%rdi
  38e18c:	call   73320 <swift_release@plt>
  38e191:	mov    -0x30(%rbp),%rdi
  38e195:	call   73320 <swift_release@plt>
  38e19a:	lea    -0xb8(%rbp),%rdi
  38e1a1:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e1a6:	lea    -0x118(%rbp),%rdi
  38e1ad:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e1b2:	mov    0x10(%rbx),%r14
  38e1b6:	mov    %rbx,%rdi
  38e1b9:	call   73320 <swift_release@plt>
  38e1be:	mov    -0x120(%rbp),%rdi
  38e1c5:	call   73320 <swift_release@plt>
  38e1ca:	mov    -0x50(%rbp),%rdi
  38e1ce:	call   73320 <swift_release@plt>
  38e1d3:	mov    $0x1,%bl
  38e1d5:	cmp    %r14,%r13
  38e1d8:	je     38e3a8 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x738>
  38e1de:	jb     38dfbc <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x34c>
  38e1e4:	ud2
  38e1e6:	lea    0x2f868b(%rip),%rcx        # 686878 <$s8FrontEnd14AssociatedTypeVN>
  38e1ed:	lea    -0x90(%rbp),%rdi
  38e1f4:	lea    -0xe8(%rbp),%rsi
  38e1fb:	mov    %rbx,%rdx
  38e1fe:	xor    %r8d,%r8d
  38e201:	call   73930 <swift_dynamicCast@plt>
  38e206:	test   %al,%al
  38e208:	je     38e2dc <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x66c>
  38e20e:	mov    -0x90(%rbp),%r13
  38e215:	mov    -0x88(%rbp),%r15
  38e21c:	mov    -0x80(%rbp),%rax
  38e220:	mov    %rax,-0x30(%rbp)
  38e224:	lea    -0xb8(%rbp),%rdi
  38e22b:	mov    %rbx,%r14
  38e22e:	lea    -0x148(%rbp),%rbx
  38e235:	mov    %rbx,%rsi
  38e238:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e23d:	lea    0x2f8634(%rip),%rcx        # 686878 <$s8FrontEnd14AssociatedTypeVN>
  38e244:	lea    -0x70(%rbp),%rdi
  38e248:	mov    $0x7,%r8d
  38e24e:	mov    %rbx,%rsi
  38e251:	mov    %r14,%rdx
  38e254:	call   73930 <swift_dynamicCast@plt>
  38e259:	mov    -0x68(%rbp),%r12
  38e25d:	cmp    -0x70(%rbp),%r13
  38e261:	jne    38e37e <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x70e>
  38e267:	mov    -0x60(%rbp),%rbx
  38e26b:	movabs $0xe000000000000000,%r14
  38e275:	mov    %r15,%rdi
  38e278:	call   1630e0 <$s8FrontEnd17WitnessExpressionV5ValueOWOy>
  38e27d:	mov    %r15,%rdi
  38e280:	mov    %r14,%rsi
  38e283:	call   3fa8f0 <$s8FrontEnd17WitnessExpressionV5ValueO21__derived_enum_equalsySbAE_AEtFZ>
  38e288:	mov    %eax,%r13d
  38e28b:	mov    %r15,%rdi
  38e28e:	call   163500 <$s8FrontEnd17WitnessExpressionV5ValueOWOe>
  38e293:	test   $0x1,%r13b
  38e297:	jne    38e2ac <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x63c>
  38e299:	mov    %r12,%rdi
  38e29c:	mov    %r14,%rsi
  38e29f:	call   3fa8f0 <$s8FrontEnd17WitnessExpressionV5ValueO21__derived_enum_equalsySbAE_AEtFZ>
  38e2a4:	test   $0x1,%al
  38e2a6:	je     38e37e <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x70e>
  38e2ac:	mov    -0x30(%rbp),%rdi
  38e2b0:	mov    %rbx,%rsi
  38e2b3:	mov    -0x38(%rbp),%rdx
  38e2b7:	mov    -0x40(%rbp),%rcx
  38e2bb:	mov    -0x48(%rbp),%r8
  38e2bf:	mov    -0xc0(%rbp),%r9
  38e2c6:	push   0x18(%rbp)
  38e2c9:	push   0x10(%rbp)
  38e2cc:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e2d1:	add    $0x10,%rsp
  38e2d5:	mov    %eax,%ebx
  38e2d7:	jmp    38e380 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x710>
  38e2dc:	lea    0x2f94c5(%rip),%rcx        # 6877a8 <$s8FrontEnd6BundleVN>
  38e2e3:	lea    -0x90(%rbp),%rdi
  38e2ea:	lea    -0xe8(%rbp),%rsi
  38e2f1:	mov    %rbx,%rdx
  38e2f4:	xor    %r8d,%r8d
  38e2f7:	call   73930 <swift_dynamicCast@plt>
  38e2fc:	test   %al,%al
  38e2fe:	je     38e3c8 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x758>
  38e304:	mov    %r14,%r13
  38e307:	mov    -0x90(%rbp),%r15
  38e30e:	movzbl -0x88(%rbp),%r12d
  38e316:	lea    -0xb8(%rbp),%rdi
  38e31d:	mov    %rbx,%r14
  38e320:	lea    -0x148(%rbp),%rbx
  38e327:	mov    %rbx,%rsi
  38e32a:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e32f:	lea    0x2f9472(%rip),%rcx        # 6877a8 <$s8FrontEnd6BundleVN>
  38e336:	lea    -0x70(%rbp),%rdi
  38e33a:	mov    $0x7,%r8d
  38e340:	mov    %rbx,%rsi
  38e343:	mov    %r14,%rdx
  38e346:	call   73930 <swift_dynamicCast@plt>
  38e34b:	cmp    -0x68(%rbp),%r12b
  38e34f:	jne    38e37a <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x70a>
  38e351:	mov    -0x70(%rbp),%rsi
  38e355:	mov    %r15,%rdi
  38e358:	mov    -0x38(%rbp),%rdx
  38e35c:	mov    -0x40(%rbp),%rcx
  38e360:	mov    -0x48(%rbp),%r8
  38e364:	mov    %r13,%r9
  38e367:	push   0x18(%rbp)
  38e36a:	push   0x10(%rbp)
  38e36d:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e372:	add    $0x10,%rsp
  38e376:	mov    %eax,%ebx
  38e378:	jmp    38e390 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x720>
  38e37a:	xor    %ebx,%ebx
  38e37c:	jmp    38e390 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x720>
  38e37e:	xor    %ebx,%ebx
  38e380:	mov    %r12,%rdi
  38e383:	call   163500 <$s8FrontEnd17WitnessExpressionV5ValueOWOe>
  38e388:	mov    %r15,%rdi
  38e38b:	call   163500 <$s8FrontEnd17WitnessExpressionV5ValueOWOe>
  38e390:	lea    -0xb8(%rbp),%rdi
  38e397:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e39c:	lea    -0x118(%rbp),%rdi
  38e3a3:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e3a8:	lea    -0xe8(%rbp),%rdi
  38e3af:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e3b4:	mov    %ebx,%eax
  38e3b6:	add    $0x128,%rsp
  38e3bd:	pop    %rbx
  38e3be:	pop    %r12
  38e3c0:	pop    %r13
  38e3c2:	pop    %r14
  38e3c4:	pop    %r15
  38e3c6:	pop    %rbp
  38e3c7:	ret
  38e3c8:	lea    0x2fcfc1(%rip),%rcx        # 68b390 <$s8FrontEnd15FunctionPointerVN>
  38e3cf:	lea    -0x90(%rbp),%rdi
  38e3d6:	lea    -0xe8(%rbp),%rsi
  38e3dd:	mov    %rbx,%rdx
  38e3e0:	xor    %r8d,%r8d
  38e3e3:	call   73930 <swift_dynamicCast@plt>
  38e3e8:	test   %al,%al
  38e3ea:	je     38e4a7 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x837>
  38e3f0:	mov    -0x90(%rbp),%r15
  38e3f7:	mov    -0x88(%rbp),%rax
  38e3fe:	mov    %rax,-0x30(%rbp)
  38e402:	lea    -0xb8(%rbp),%rdi
  38e409:	mov    %r14,%r12
  38e40c:	mov    %rbx,%r14
  38e40f:	lea    -0x148(%rbp),%rbx
  38e416:	mov    %rbx,%rsi
  38e419:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e41e:	lea    0x2fcf6b(%rip),%rcx        # 68b390 <$s8FrontEnd15FunctionPointerVN>
  38e425:	lea    -0x70(%rbp),%rdi
  38e429:	mov    $0x7,%r8d
  38e42f:	mov    %rbx,%rsi
  38e432:	mov    %r14,%rdx
  38e435:	mov    %r12,%r14
  38e438:	call   73930 <swift_dynamicCast@plt>
  38e43d:	mov    -0x70(%rbp),%r12
  38e441:	mov    -0x68(%rbp),%rax
  38e445:	mov    %rax,-0x50(%rbp)
  38e449:	mov    0x10(%r15),%r13
  38e44d:	xor    %ebx,%ebx
  38e44f:	cmp    %rbx,%r13
  38e452:	je     38e61d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x9ad>
  38e458:	cmp    0x10(%r15),%rbx
  38e45c:	jae    38e806 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb96>
  38e462:	cmp    0x10(%r12),%rbx
  38e467:	je     38e57d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x90d>
  38e46d:	jae    38e808 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb98>
  38e473:	mov    0x20(%r15,%rbx,8),%rdi
  38e478:	mov    0x20(%r12,%rbx,8),%rsi
  38e47d:	mov    -0x38(%rbp),%rdx
  38e481:	mov    -0x40(%rbp),%rcx
  38e485:	mov    -0x48(%rbp),%r8
  38e489:	mov    %r14,%r9
  38e48c:	push   0x18(%rbp)
  38e48f:	push   0x10(%rbp)
  38e492:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e497:	add    $0x10,%rsp
  38e49b:	inc    %rbx
  38e49e:	test   $0x1,%al
  38e4a0:	jne    38e44f <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x7df>
  38e4a2:	jmp    38e57d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x90d>
  38e4a7:	lea    0x30299a(%rip),%rcx        # 690e48 <$s8FrontEnd11ImplicationVN>
  38e4ae:	lea    -0x90(%rbp),%rdi
  38e4b5:	lea    -0xe8(%rbp),%rsi
  38e4bc:	mov    %rbx,%rdx
  38e4bf:	xor    %r8d,%r8d
  38e4c2:	call   73930 <swift_dynamicCast@plt>
  38e4c7:	test   %al,%al
  38e4c9:	je     38e584 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x914>
  38e4cf:	mov    -0x90(%rbp),%r15
  38e4d6:	mov    -0x88(%rbp),%rax
  38e4dd:	mov    %rax,-0x30(%rbp)
  38e4e1:	lea    -0xb8(%rbp),%rdi
  38e4e8:	mov    %r14,%r12
  38e4eb:	mov    %rbx,%r14
  38e4ee:	lea    -0x148(%rbp),%rbx
  38e4f5:	mov    %rbx,%rsi
  38e4f8:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e4fd:	lea    0x302944(%rip),%rcx        # 690e48 <$s8FrontEnd11ImplicationVN>
  38e504:	lea    -0x70(%rbp),%rdi
  38e508:	mov    $0x7,%r8d
  38e50e:	mov    %rbx,%rsi
  38e511:	mov    %r14,%rdx
  38e514:	mov    %r12,%r14
  38e517:	call   73930 <swift_dynamicCast@plt>
  38e51c:	mov    -0x70(%rbp),%r12
  38e520:	mov    -0x68(%rbp),%rax
  38e524:	mov    %rax,-0x50(%rbp)
  38e528:	mov    0x10(%r15),%r13
  38e52c:	xor    %ebx,%ebx
  38e52e:	cmp    %rbx,%r13
  38e531:	je     38e6bb <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa4b>
  38e537:	cmp    0x10(%r15),%rbx
  38e53b:	jae    38e80a <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb9a>
  38e541:	cmp    0x10(%r12),%rbx
  38e546:	je     38e57d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x90d>
  38e548:	jae    38e80c <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb9c>
  38e54e:	mov    0x20(%r15,%rbx,8),%rdi
  38e553:	mov    0x20(%r12,%rbx,8),%rsi
  38e558:	mov    -0x38(%rbp),%rdx
  38e55c:	mov    -0x40(%rbp),%rcx
  38e560:	mov    -0x48(%rbp),%r8
  38e564:	mov    %r14,%r9
  38e567:	push   0x18(%rbp)
  38e56a:	push   0x10(%rbp)
  38e56d:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e572:	add    $0x10,%rsp
  38e576:	inc    %rbx
  38e579:	test   $0x1,%al
  38e57b:	jne    38e52e <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x8be>
  38e57d:	xor    %ebx,%ebx
  38e57f:	jmp    38e6ee <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa7e>
  38e584:	lea    0x304f4d(%rip),%rcx        # 6934d8 <$s8FrontEnd8MetatypeVN>
  38e58b:	lea    -0x90(%rbp),%rdi
  38e592:	lea    -0xe8(%rbp),%rsi
  38e599:	mov    %rbx,%rdx
  38e59c:	xor    %r8d,%r8d
  38e59f:	call   73930 <swift_dynamicCast@plt>
  38e5a4:	test   %al,%al
  38e5a6:	je     38e660 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x9f0>
  38e5ac:	mov    %r14,%r13
  38e5af:	mov    %rbx,%r14
  38e5b2:	mov    -0x90(%rbp),%rbx
  38e5b9:	lea    -0xb8(%rbp),%r15
  38e5c0:	lea    -0x148(%rbp),%r12
  38e5c7:	mov    %r15,%rdi
  38e5ca:	mov    %r12,%rsi
  38e5cd:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e5d2:	lea    0x304eff(%rip),%rcx        # 6934d8 <$s8FrontEnd8MetatypeVN>
  38e5d9:	lea    -0x70(%rbp),%rdi
  38e5dd:	mov    $0x7,%r8d
  38e5e3:	mov    %r12,%rsi
  38e5e6:	mov    %r14,%rdx
  38e5e9:	call   73930 <swift_dynamicCast@plt>
  38e5ee:	mov    -0x70(%rbp),%rsi
  38e5f2:	mov    %rbx,%rdi
  38e5f5:	mov    -0x38(%rbp),%rdx
  38e5f9:	mov    -0x40(%rbp),%rcx
  38e5fd:	mov    -0x48(%rbp),%r8
  38e601:	mov    %r13,%r9
  38e604:	push   0x18(%rbp)
  38e607:	push   0x10(%rbp)
  38e60a:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e60f:	add    $0x10,%rsp
  38e613:	mov    %eax,%ebx
  38e615:	mov    %r15,%rdi
  38e618:	jmp    38e397 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x727>
  38e61d:	cmp    0x10(%r12),%r13
  38e622:	je     38e6c6 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa56>
  38e628:	mov    %r15,%rdi
  38e62b:	call   73320 <swift_release@plt>
  38e630:	lea    -0xb8(%rbp),%rdi
  38e637:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e63c:	lea    -0x118(%rbp),%rdi
  38e643:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e648:	mov    0x10(%r12),%rbx
  38e64d:	mov    %r12,%rdi
  38e650:	call   73320 <swift_release@plt>
  38e655:	cmp    %rbx,%r13
  38e658:	jb     38dfbc <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x34c>
  38e65e:	ud2
  38e660:	lea    0x307739(%rip),%rcx        # 695da0 <$s8FrontEnd10RemoteTypeVN>
  38e667:	lea    -0x90(%rbp),%rdi
  38e66e:	lea    -0xe8(%rbp),%rsi
  38e675:	mov    %rbx,%rdx
  38e678:	xor    %r8d,%r8d
  38e67b:	call   73930 <swift_dynamicCast@plt>
  38e680:	test   %al,%al
  38e682:	je     38e702 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa92>
  38e684:	mov    %r14,%r13
  38e687:	mov    -0x90(%rbp),%r15
  38e68e:	movzbl -0x88(%rbp),%r12d
  38e696:	lea    -0xb8(%rbp),%rdi
  38e69d:	mov    %rbx,%r14
  38e6a0:	lea    -0x148(%rbp),%rbx
  38e6a7:	mov    %rbx,%rsi
  38e6aa:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e6af:	lea    0x3076ea(%rip),%rcx        # 695da0 <$s8FrontEnd10RemoteTypeVN>
  38e6b6:	jmp    38e336 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x6c6>
  38e6bb:	cmp    0x10(%r12),%r13
  38e6c0:	jne    38e7aa <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb3a>
  38e6c6:	mov    -0x30(%rbp),%rdi
  38e6ca:	mov    -0x50(%rbp),%rsi
  38e6ce:	mov    -0x38(%rbp),%rdx
  38e6d2:	mov    -0x40(%rbp),%rcx
  38e6d6:	mov    -0x48(%rbp),%r8
  38e6da:	mov    %r14,%r9
  38e6dd:	push   0x18(%rbp)
  38e6e0:	push   0x10(%rbp)
  38e6e3:	call   396da0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF>
  38e6e8:	add    $0x10,%rsp
  38e6ec:	mov    %eax,%ebx
  38e6ee:	mov    %r15,%rdi
  38e6f1:	call   73320 <swift_release@plt>
  38e6f6:	mov    %r12,%rdi
  38e6f9:	jmp    38df61 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x2f1>
  38e6fe:	ud2
  38e700:	ud2
  38e702:	lea    0x30c87f(%rip),%rcx        # 69af88 <$s8FrontEnd13UniversalTypeVN>
  38e709:	lea    -0x90(%rbp),%rdi
  38e710:	lea    -0xe8(%rbp),%rsi
  38e717:	mov    %rbx,%rdx
  38e71a:	xor    %r8d,%r8d
  38e71d:	call   73930 <swift_dynamicCast@plt>
  38e722:	test   %al,%al
  38e724:	je     38e7e2 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb72>
  38e72a:	mov    %r14,%r13
  38e72d:	mov    -0x90(%rbp),%r15
  38e734:	mov    -0x88(%rbp),%rax
  38e73b:	mov    %rax,-0x30(%rbp)
  38e73f:	lea    -0xb8(%rbp),%rdi
  38e746:	mov    %rbx,%r14
  38e749:	lea    -0x148(%rbp),%rbx
  38e750:	mov    %rbx,%rsi
  38e753:	call   15e8e0 <$s8FrontEnd8TypeTree_pWOc>
  38e758:	lea    0x30c829(%rip),%rcx        # 69af88 <$s8FrontEnd13UniversalTypeVN>
  38e75f:	lea    -0x70(%rbp),%rdi
  38e763:	mov    $0x7,%r8d
  38e769:	mov    %rbx,%rsi
  38e76c:	mov    %r14,%rdx
  38e76f:	call   73930 <swift_dynamicCast@plt>
  38e774:	mov    -0x70(%rbp),%r12
  38e778:	mov    -0x68(%rbp),%rbx
  38e77c:	mov    %r12,%rdi
  38e77f:	mov    %r15,%rsi
  38e782:	call   2911d0 <$sSTsSQ7ElementRpzrlE13elementsEqualySbqd__STRd__AAQyd__ABRSlFSay8FrontEnd20ConcreteTypeIdentityVyAE16GenericParameterOGG_AKTg5>
  38e787:	test   $0x1,%al
  38e789:	je     38e57d <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x90d>
  38e78f:	mov    -0x30(%rbp),%rdi
  38e793:	mov    %rbx,%rsi
  38e796:	mov    -0x38(%rbp),%rdx
  38e79a:	mov    -0x40(%rbp),%rcx
  38e79e:	mov    -0x48(%rbp),%r8
  38e7a2:	mov    %r13,%r9
  38e7a5:	jmp    38e6dd <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xa6d>
  38e7aa:	mov    %r15,%rdi
  38e7ad:	call   73320 <swift_release@plt>
  38e7b2:	lea    -0xb8(%rbp),%rdi
  38e7b9:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e7be:	lea    -0x118(%rbp),%rdi
  38e7c5:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e7ca:	mov    0x10(%r12),%rbx
  38e7cf:	mov    %r12,%rdi
  38e7d2:	call   73320 <swift_release@plt>
  38e7d7:	cmp    %rbx,%r13
  38e7da:	jb     38dfbc <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0x34c>
  38e7e0:	ud2
  38e7e2:	lea    -0xb8(%rbp),%rdi
  38e7e9:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e7ee:	lea    -0x118(%rbp),%rdi
  38e7f5:	call   1015f0 <__swift_destroy_boxed_opaque_existential_1>
  38e7fa:	lea    -0xe8(%rbp),%rdi
  38e801:	jmp    38dd26 <$s8FrontEnd9TypeStoreV18unifiableSameShape33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AiA17SubstitutionTableVzSbAI_AItXEtF+0xb6>
  38e806:	ud2
  38e808:	ud2
  38e80a:	ud2
  38e80c:	ud2
  38e80e:	xchg   %ax,%ax

000000000038e810 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n>:
  38e810:	push   %rbp
  38e811:	mov    %rsp,%rbp
  38e814:	push   %r15
  38e816:	push   %r14
  38e818:	push   %r13
  38e81a:	push   %r12
  38e81c:	push   %rbx
  38e81d:	sub    $0x78,%rsp
  38e821:	mov    %rcx,-0xa0(%rbp)
  38e828:	mov    %rdx,-0x30(%rbp)
  38e82c:	cmp    %r8w,%di
  38e830:	jne    38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38e836:	mov    %rsi,-0x98(%rbp)
  38e83d:	mov    %r9,-0x48(%rbp)
  38e841:	mov    0x38(%rbp),%rax
  38e845:	mov    %rax,-0x68(%rbp)
  38e849:	mov    0x30(%rbp),%rax
  38e84d:	mov    %rax,-0x60(%rbp)
  38e851:	mov    0x28(%rbp),%rax
  38e855:	mov    %rax,-0x58(%rbp)
  38e859:	mov    0x20(%rbp),%rax
  38e85d:	mov    %rax,-0x50(%rbp)
  38e861:	mov    0x18(%rbp),%rax
  38e865:	mov    %rax,-0x90(%rbp)
  38e86c:	mov    0x10(%rbp),%rbx
  38e870:	mov    -0x30(%rbp),%rdi
  38e874:	mov    0x10(%rdi),%rax
  38e878:	mov    %rax,-0x40(%rbp)
  38e87c:	mov    0x10(%rbx),%r14
  38e880:	call   731a0 <swift_retain@plt>
  38e885:	mov    %rbx,%rdi
  38e888:	call   731a0 <swift_retain@plt>
  38e88d:	mov    %rbx,-0x38(%rbp)
  38e891:	lea    0x28(%rbx),%r15
  38e895:	xor    %ebx,%ebx
  38e897:	mov    %r14,-0x88(%rbp)
  38e89e:	jmp    38e8b5 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0xa5>
  38e8a0:	test   %r15,%r15
  38e8a3:	jne    38e9bc <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x1ac>
  38e8a9:	mov    -0x78(%rbp),%r15
  38e8ad:	add    $0x30,%r15
  38e8b1:	mov    -0x80(%rbp),%rbx
  38e8b5:	cmp    -0x40(%rbp),%rbx
  38e8b9:	jne    38e8e0 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0xd0>
  38e8bb:	test   %r14,%r14
  38e8be:	je     38e9d1 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x1c1>
  38e8c4:	mov    $0x1,%r12d
  38e8ca:	mov    -0x40(%rbp),%rbx
  38e8ce:	xor    %r13d,%r13d
  38e8d1:	jmp    38e910 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x100>
  38e8d3:	data16 data16 data16 cs nopw 0x0(%rax,%rax,1)
  38e8e0:	jae    38ebb8 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x3a8>
  38e8e6:	lea    (%rbx,%rbx,2),%rax
  38e8ea:	shl    $0x4,%rax
  38e8ee:	mov    -0x30(%rbp),%rcx
  38e8f2:	mov    0x20(%rcx,%rax,1),%r13
  38e8f7:	mov    0x28(%rcx,%rax,1),%r12
  38e8fc:	mov    %r12,%rdi
  38e8ff:	call   73af0 <swift_bridgeObjectRetain@plt>
  38e904:	test   %r14,%r14
  38e907:	je     38e9c7 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x1b7>
  38e90d:	inc    %rbx
  38e910:	sub    $0x1,%r14
  38e914:	jb     38ebb6 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x3a6>
  38e91a:	mov    %rbx,-0x80(%rbp)
  38e91e:	mov    -0x8(%r15),%rbx
  38e922:	mov    %r15,-0x78(%rbp)
  38e926:	mov    (%r15),%r15
  38e929:	mov    %r15,%rdi
  38e92c:	call   73af0 <swift_bridgeObjectRetain@plt>
  38e931:	cmp    $0x1,%r12
  38e935:	je     38e9b6 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x1a6>
  38e937:	cmp    $0x1,%r15
  38e93b:	je     38eb34 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x324>
  38e941:	test   %r12,%r12
  38e944:	je     38e8a0 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x90>
  38e94a:	test   %r15,%r15
  38e94d:	je     38eb34 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x324>
  38e953:	mov    %r13,%rax
  38e956:	xor    %rbx,%rax
  38e959:	mov    %r12,%rcx
  38e95c:	xor    %r15,%rcx
  38e95f:	mov    %r13,%rdi
  38e962:	mov    %r12,%rsi
  38e965:	or     %rax,%rcx
  38e968:	jne    38e980 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x170>
  38e96a:	call   291f50 <$sSSSgSgWOe>
  38e96f:	mov    %r13,%rdi
  38e972:	mov    %r12,%rsi
  38e975:	call   291f50 <$sSSSgSgWOe>
  38e97a:	jmp    38e8a9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x99>
  38e97f:	nop
  38e980:	mov    %rbx,%rdx
  38e983:	mov    %r15,%rcx
  38e986:	xor    %r8d,%r8d
  38e989:	call   73fd0 <$ss27_stringCompareWithSmolCheck__9expectingSbs11_StringGutsV_ADs01_G16ComparisonResultOtF@plt>
  38e98e:	mov    %al,-0x70(%rbp)
  38e991:	mov    %rbx,%rdi
  38e994:	mov    %r15,%rsi
  38e997:	call   291f50 <$sSSSgSgWOe>
  38e99c:	mov    %r13,%rdi
  38e99f:	mov    %r12,%rsi
  38e9a2:	call   291f50 <$sSSSgSgWOe>
  38e9a7:	testb  $0x1,-0x70(%rbp)
  38e9ab:	jne    38e8a9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x99>
  38e9b1:	jmp    38eb3f <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x32f>
  38e9b6:	cmp    $0x1,%r15
  38e9ba:	je     38e9d1 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x1c1>
  38e9bc:	mov    %rbx,%rdi
  38e9bf:	mov    %r15,%rsi
  38e9c2:	jmp    38eb3a <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x32a>
  38e9c7:	cmp    $0x1,%r12
  38e9cb:	jne    38eb34 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x324>
  38e9d1:	mov    -0x30(%rbp),%rdi
  38e9d5:	call   73320 <swift_release@plt>
  38e9da:	mov    -0x38(%rbp),%rdi
  38e9de:	call   73320 <swift_release@plt>
  38e9e3:	mov    -0x98(%rbp),%rdi
  38e9ea:	mov    -0x48(%rbp),%rsi
  38e9ee:	mov    -0x50(%rbp),%rdx
  38e9f2:	mov    -0x58(%rbp),%rcx
  38e9f6:	mov    -0x60(%rbp),%r8
  38e9fa:	mov    -0x68(%rbp),%r9
  38e9fe:	call   389080 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF03$s8a4End9cd16V9unifiableyAA17lm7VSgAA03j2C8k11V_AItFSbAI_U5XEfU_Tf1nnncn_n>
  38ea03:	test   $0x1,%al
  38ea05:	je     38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38ea0b:	mov    -0x88(%rbp),%rax
  38ea12:	inc    %rax
  38ea15:	mov    %rax,-0x48(%rbp)
  38ea19:	mov    $0x38,%r14d
  38ea1f:	xor    %r13d,%r13d
  38ea22:	data16 data16 data16 data16 cs nopw 0x0(%rax,%rax,1)
  38ea30:	cmp    %r13,-0x40(%rbp)
  38ea34:	je     38eb62 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x352>
  38ea3a:	inc    %r13
  38ea3d:	cmp    %r13,-0x48(%rbp)
  38ea41:	je     38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38ea47:	mov    -0x30(%rbp),%rax
  38ea4b:	mov    -0x10(%rax,%r14,1),%r15
  38ea50:	movzbl -0x8(%rax,%r14,1),%esi
  38ea56:	mov    (%rax,%r14,1),%rbx
  38ea5a:	mov    -0x38(%rbp),%rax
  38ea5e:	mov    -0x10(%rax,%r14,1),%r12
  38ea63:	movzbl -0x8(%rax,%r14,1),%r9d
  38ea69:	mov    (%rax,%r14,1),%r8
  38ea6d:	test   %r15,%r15
  38ea70:	je     38eaea <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x2da>
  38ea72:	test   %r12,%r12
  38ea75:	je     38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38ea7b:	mov    -0x30(%rbp),%rax
  38ea7f:	mov    -0x18(%rax,%r14,1),%rdi
  38ea84:	mov    -0x38(%rbp),%rax
  38ea88:	mov    -0x18(%rax,%r14,1),%rdx
  38ea8d:	mov    %rdi,%rax
  38ea90:	xor    %rdx,%rax
  38ea93:	mov    %r15,%rcx
  38ea96:	xor    %r12,%rcx
  38ea99:	or     %rax,%rcx
  38ea9c:	mov    %rbx,-0x80(%rbp)
  38eaa0:	mov    %sil,-0x78(%rbp)
  38eaa4:	mov    %r8,-0x70(%rbp)
  38eaa8:	je     38eac6 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x2b6>
  38eaaa:	mov    %r15,%rsi
  38eaad:	mov    %r12,%rcx
  38eab0:	xor    %r8d,%r8d
  38eab3:	mov    %r9d,%ebx
  38eab6:	call   73fd0 <$ss27_stringCompareWithSmolCheck__9expectingSbs11_StringGutsV_ADs01_G16ComparisonResultOtF@plt>
  38eabb:	mov    %ebx,%r9d
  38eabe:	test   $0x1,%al
  38eac0:	je     38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38eac6:	mov    %r12,%rdi
  38eac9:	mov    %r9d,%ebx
  38eacc:	call   73af0 <swift_bridgeObjectRetain@plt>
  38ead1:	mov    %r15,%rdi
  38ead4:	call   73af0 <swift_bridgeObjectRetain@plt>
  38ead9:	mov    %ebx,%r9d
  38eadc:	movzbl -0x78(%rbp),%esi
  38eae0:	mov    -0x70(%rbp),%r8
  38eae4:	mov    -0x80(%rbp),%rbx
  38eae8:	jmp    38eaef <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x2df>
  38eaea:	test   %r12,%r12
  38eaed:	jne    38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38eaef:	cmp    %r9b,%sil
  38eaf2:	jne    38eba0 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x390>
  38eaf8:	add    $0x30,%r14
  38eafc:	mov    %rbx,%rdi
  38eaff:	mov    %r8,%rsi
  38eb02:	mov    -0x50(%rbp),%rdx
  38eb06:	mov    -0x58(%rbp),%rcx
  38eb0a:	mov    -0x60(%rbp),%r8
  38eb0e:	mov    -0x68(%rbp),%r9
  38eb12:	call   389080 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF03$s8a4End9cd16V9unifiableyAA17lm7VSgAA03j2C8k11V_AItFSbAI_U5XEfU_Tf1nnncn_n>
  38eb17:	mov    %eax,%ebx
  38eb19:	mov    %r12,%rdi
  38eb1c:	call   737b0 <swift_bridgeObjectRelease@plt>
  38eb21:	mov    %r15,%rdi
  38eb24:	call   737b0 <swift_bridgeObjectRelease@plt>
  38eb29:	test   $0x1,%bl
  38eb2c:	jne    38ea30 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x220>
  38eb32:	jmp    38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38eb34:	mov    %r13,%rdi
  38eb37:	mov    %r12,%rsi
  38eb3a:	call   291f50 <$sSSSgSgWOe>
  38eb3f:	mov    -0x30(%rbp),%rdi
  38eb43:	call   73320 <swift_release@plt>
  38eb48:	mov    -0x38(%rbp),%rdi
  38eb4c:	call   73320 <swift_release@plt>
  38eb51:	xor    %eax,%eax
  38eb53:	add    $0x78,%rsp
  38eb57:	pop    %rbx
  38eb58:	pop    %r12
  38eb5a:	pop    %r13
  38eb5c:	pop    %r14
  38eb5e:	pop    %r15
  38eb60:	pop    %rbp
  38eb61:	ret
  38eb62:	mov    -0x88(%rbp),%rax
  38eb69:	cmp    %rax,-0x40(%rbp)
  38eb6d:	jne    38ebb2 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x3a2>
  38eb6f:	mov    -0xa0(%rbp),%rdi
  38eb76:	mov    -0x90(%rbp),%rsi
  38eb7d:	mov    -0x50(%rbp),%rdx
  38eb81:	mov    -0x58(%rbp),%rcx
  38eb85:	mov    -0x60(%rbp),%r8
  38eb89:	mov    -0x68(%rbp),%r9
  38eb8d:	add    $0x78,%rsp
  38eb91:	pop    %rbx
  38eb92:	pop    %r12
  38eb94:	pop    %r13
  38eb96:	pop    %r14
  38eb98:	pop    %r15
  38eb9a:	pop    %rbp
  38eb9b:	jmp    389080 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF03$s8a4End9cd16V9unifiableyAA17lm7VSgAA03j2C8k11V_AItFSbAI_U5XEfU_Tf1nnncn_n>
  38eba0:	mov    %r12,%rdi
  38eba3:	call   737b0 <swift_bridgeObjectRelease@plt>
  38eba8:	mov    %r15,%rdi
  38ebab:	call   737b0 <swift_bridgeObjectRelease@plt>
  38ebb0:	jmp    38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38ebb2:	jb     38eb51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a4End9cd16V9unifiableyAA17pq7VSgAA03r2C8S19V_AItFSbAI_AItXEfU_Tf1nnncn_n+0x341>
  38ebb4:	ud2
  38ebb6:	ud2
  38ebb8:	ud2
  38ebba:	nopw   0x0(%rax,%rax,1)

000000000038ebc0 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n>:
  38ebc0:	push   %rbp
  38ebc1:	mov    %rsp,%rbp
  38ebc4:	push   %r15
  38ebc6:	push   %r14
  38ebc8:	push   %r13
  38ebca:	push   %r12
  38ebcc:	push   %rbx
  38ebcd:	sub    $0x58,%rsp
  38ebd1:	mov    %rcx,-0x70(%rbp)
  38ebd5:	mov    %rdx,-0x30(%rbp)
  38ebd9:	cmp    %r8w,%di
  38ebdd:	jne    38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38ebe3:	mov    %rsi,-0x68(%rbp)
  38ebe7:	mov    %r9,-0x40(%rbp)
  38ebeb:	mov    0x10(%rbp),%rbx
  38ebef:	mov    -0x30(%rbp),%rdi
  38ebf3:	mov    0x10(%rdi),%rax
  38ebf7:	mov    %rax,-0x38(%rbp)
  38ebfb:	mov    0x10(%rbx),%r14
  38ebff:	call   731a0 <swift_retain@plt>
  38ec04:	mov    %rbx,%rdi
  38ec07:	call   731a0 <swift_retain@plt>
  38ec0c:	add    $0x28,%rbx
  38ec10:	xor    %r12d,%r12d
  38ec13:	mov    %r14,-0x60(%rbp)
  38ec17:	jmp    38ec35 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x75>
  38ec19:	nopl   0x0(%rax)
  38ec20:	test   %rbx,%rbx
  38ec23:	jne    38ed3c <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x17c>
  38ec29:	mov    -0x50(%rbp),%rbx
  38ec2d:	add    $0x30,%rbx
  38ec31:	mov    -0x58(%rbp),%r12
  38ec35:	cmp    -0x38(%rbp),%r12
  38ec39:	jne    38ec60 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0xa0>
  38ec3b:	test   %r14,%r14
  38ec3e:	je     38ed51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x191>
  38ec44:	mov    $0x1,%r15d
  38ec4a:	mov    -0x38(%rbp),%r12
  38ec4e:	xor    %r13d,%r13d
  38ec51:	jmp    38ec90 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0xd0>
  38ec53:	data16 data16 data16 cs nopw 0x0(%rax,%rax,1)
  38ec60:	jae    38ef33 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x373>
  38ec66:	lea    (%r12,%r12,2),%rax
  38ec6a:	shl    $0x4,%rax
  38ec6e:	mov    -0x30(%rbp),%rcx
  38ec72:	mov    0x20(%rcx,%rax,1),%r13
  38ec77:	mov    0x28(%rcx,%rax,1),%r15
  38ec7c:	mov    %r15,%rdi
  38ec7f:	call   73af0 <swift_bridgeObjectRetain@plt>
  38ec84:	test   %r14,%r14
  38ec87:	je     38ed47 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x187>
  38ec8d:	inc    %r12
  38ec90:	sub    $0x1,%r14
  38ec94:	jb     38ef31 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x371>
  38ec9a:	mov    %r12,-0x58(%rbp)
  38ec9e:	mov    -0x8(%rbx),%r12
  38eca2:	mov    %rbx,-0x50(%rbp)
  38eca6:	mov    (%rbx),%rbx
  38eca9:	mov    %rbx,%rdi
  38ecac:	call   73af0 <swift_bridgeObjectRetain@plt>
  38ecb1:	cmp    $0x1,%r15
  38ecb5:	je     38ed36 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x176>
  38ecb7:	cmp    $0x1,%rbx
  38ecbb:	je     38eebc <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x2fc>
  38ecc1:	test   %r15,%r15
  38ecc4:	je     38ec20 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x60>
  38ecca:	test   %rbx,%rbx
  38eccd:	je     38eebc <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x2fc>
  38ecd3:	mov    %r13,%rax
  38ecd6:	xor    %r12,%rax
  38ecd9:	mov    %r15,%rcx
  38ecdc:	xor    %rbx,%rcx
  38ecdf:	mov    %r13,%rdi
  38ece2:	mov    %r15,%rsi
  38ece5:	or     %rax,%rcx
  38ece8:	jne    38ed00 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x140>
  38ecea:	call   291f50 <$sSSSgSgWOe>
  38ecef:	mov    %r13,%rdi
  38ecf2:	mov    %r15,%rsi
  38ecf5:	call   291f50 <$sSSSgSgWOe>
  38ecfa:	jmp    38ec29 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x69>
  38ecff:	nop
  38ed00:	mov    %r12,%rdx
  38ed03:	mov    %rbx,%rcx
  38ed06:	xor    %r8d,%r8d
  38ed09:	call   73fd0 <$ss27_stringCompareWithSmolCheck__9expectingSbs11_StringGutsV_ADs01_G16ComparisonResultOtF@plt>
  38ed0e:	mov    %al,-0x48(%rbp)
  38ed11:	mov    %r12,%rdi
  38ed14:	mov    %rbx,%rsi
  38ed17:	call   291f50 <$sSSSgSgWOe>
  38ed1c:	mov    %r13,%rdi
  38ed1f:	mov    %r15,%rsi
  38ed22:	call   291f50 <$sSSSgSgWOe>
  38ed27:	testb  $0x1,-0x48(%rbp)
  38ed2b:	jne    38ec29 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x69>
  38ed31:	jmp    38eec7 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x307>
  38ed36:	cmp    $0x1,%rbx
  38ed3a:	je     38ed51 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x191>
  38ed3c:	mov    %r12,%rdi
  38ed3f:	mov    %rbx,%rsi
  38ed42:	jmp    38eec2 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x302>
  38ed47:	cmp    $0x1,%r15
  38ed4b:	jne    38eebc <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x2fc>
  38ed51:	mov    -0x30(%rbp),%rdi
  38ed55:	call   73320 <swift_release@plt>
  38ed5a:	mov    0x10(%rbp),%rdi
  38ed5e:	call   73320 <swift_release@plt>
  38ed63:	mov    0x40(%rbp),%rax
  38ed67:	mov    %rax,(%rsp)
  38ed6b:	mov    -0x68(%rbp),%rdi
  38ed6f:	mov    -0x40(%rbp),%rsi
  38ed73:	mov    0x20(%rbp),%rdx
  38ed77:	mov    0x28(%rbp),%rcx
  38ed7b:	mov    0x30(%rbp),%r8
  38ed7f:	mov    0x38(%rbp),%r9
  38ed83:	call   389ef0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopek9VtFSbAA07jC12R0V_ANtXEfU_SayAH_AHtGTf1nnncn_n>
  38ed88:	test   $0x1,%al
  38ed8a:	je     38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38ed90:	mov    -0x60(%rbp),%rax
  38ed94:	inc    %rax
  38ed97:	mov    %rax,-0x40(%rbp)
  38ed9b:	mov    $0x38,%r14d
  38eda1:	xor    %r13d,%r13d
  38eda4:	data16 data16 cs nopw 0x0(%rax,%rax,1)
  38edb0:	cmp    %r13,-0x38(%rbp)
  38edb4:	je     38eeea <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x32a>
  38edba:	inc    %r13
  38edbd:	cmp    %r13,-0x40(%rbp)
  38edc1:	je     38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38edc7:	mov    -0x30(%rbp),%rax
  38edcb:	mov    -0x10(%rax,%r14,1),%r15
  38edd0:	movzbl -0x8(%rax,%r14,1),%esi
  38edd6:	mov    (%rax,%r14,1),%rbx
  38edda:	mov    0x10(%rbp),%rax
  38edde:	mov    -0x10(%rax,%r14,1),%r12
  38ede3:	movzbl -0x8(%rax,%r14,1),%r9d
  38ede9:	mov    (%rax,%r14,1),%r8
  38eded:	test   %r15,%r15
  38edf0:	je     38ee6a <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x2aa>
  38edf2:	test   %r12,%r12
  38edf5:	je     38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38edfb:	mov    -0x30(%rbp),%rax
  38edff:	mov    -0x18(%rax,%r14,1),%rdi
  38ee04:	mov    0x10(%rbp),%rax
  38ee08:	mov    -0x18(%rax,%r14,1),%rdx
  38ee0d:	mov    %rdi,%rax
  38ee10:	xor    %rdx,%rax
  38ee13:	mov    %r15,%rcx
  38ee16:	xor    %r12,%rcx
  38ee19:	or     %rax,%rcx
  38ee1c:	mov    %rbx,-0x58(%rbp)
  38ee20:	mov    %sil,-0x50(%rbp)
  38ee24:	mov    %r8,-0x48(%rbp)
  38ee28:	je     38ee46 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x286>
  38ee2a:	mov    %r15,%rsi
  38ee2d:	mov    %r12,%rcx
  38ee30:	xor    %r8d,%r8d
  38ee33:	mov    %r9d,%ebx
  38ee36:	call   73fd0 <$ss27_stringCompareWithSmolCheck__9expectingSbs11_StringGutsV_ADs01_G16ComparisonResultOtF@plt>
  38ee3b:	mov    %ebx,%r9d
  38ee3e:	test   $0x1,%al
  38ee40:	je     38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38ee46:	mov    %r12,%rdi
  38ee49:	mov    %r9d,%ebx
  38ee4c:	call   73af0 <swift_bridgeObjectRetain@plt>
  38ee51:	mov    %r15,%rdi
  38ee54:	call   73af0 <swift_bridgeObjectRetain@plt>
  38ee59:	mov    %ebx,%r9d
  38ee5c:	movzbl -0x50(%rbp),%esi
  38ee60:	mov    -0x48(%rbp),%r8
  38ee64:	mov    -0x58(%rbp),%rbx
  38ee68:	jmp    38ee6f <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x2af>
  38ee6a:	test   %r12,%r12
  38ee6d:	jne    38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38ee6f:	cmp    %r9b,%sil
  38ee72:	jne    38ef1b <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x35b>
  38ee78:	add    $0x30,%r14
  38ee7c:	mov    0x40(%rbp),%rax
  38ee80:	mov    %rax,(%rsp)
  38ee84:	mov    %rbx,%rdi
  38ee87:	mov    %r8,%rsi
  38ee8a:	mov    0x20(%rbp),%rdx
  38ee8e:	mov    0x28(%rbp),%rcx
  38ee92:	mov    0x30(%rbp),%r8
  38ee96:	mov    0x38(%rbp),%r9
  38ee9a:	call   389ef0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopek9VtFSbAA07jC12R0V_ANtXEfU_SayAH_AHtGTf1nnncn_n>
  38ee9f:	mov    %eax,%ebx
  38eea1:	mov    %r12,%rdi
  38eea4:	call   737b0 <swift_bridgeObjectRelease@plt>
  38eea9:	mov    %r15,%rdi
  38eeac:	call   737b0 <swift_bridgeObjectRelease@plt>
  38eeb1:	test   $0x1,%bl
  38eeb4:	jne    38edb0 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x1f0>
  38eeba:	jmp    38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38eebc:	mov    %r13,%rdi
  38eebf:	mov    %r15,%rsi
  38eec2:	call   291f50 <$sSSSgSgWOe>
  38eec7:	mov    -0x30(%rbp),%rdi
  38eecb:	call   73320 <swift_release@plt>
  38eed0:	mov    0x10(%rbp),%rdi
  38eed4:	call   73320 <swift_release@plt>
  38eed9:	xor    %eax,%eax
  38eedb:	add    $0x58,%rsp
  38eedf:	pop    %rbx
  38eee0:	pop    %r12
  38eee2:	pop    %r13
  38eee4:	pop    %r14
  38eee6:	pop    %r15
  38eee8:	pop    %rbp
  38eee9:	ret
  38eeea:	mov    -0x60(%rbp),%rax
  38eeee:	cmp    %rax,-0x38(%rbp)
  38eef2:	jne    38ef2d <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x36d>
  38eef4:	mov    0x40(%rbp),%rax
  38eef8:	mov    %rax,(%rsp)
  38eefc:	mov    -0x70(%rbp),%rdi
  38ef00:	mov    0x18(%rbp),%rsi
  38ef04:	mov    0x20(%rbp),%rdx
  38ef08:	mov    0x28(%rbp),%rcx
  38ef0c:	mov    0x30(%rbp),%r8
  38ef10:	mov    0x38(%rbp),%r9
  38ef14:	call   389ef0 <$s8FrontEnd9TypeStoreV9unifiable__9extending21handlingCoercionsWithSbAA03AnyC8IdentityV_AhA17SubstitutionTableVzSbAH_AHtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopek9VtFSbAA07jC12R0V_ANtXEfU_SayAH_AHtGTf1nnncn_n>
  38ef19:	jmp    38eedb <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x31b>
  38ef1b:	mov    %r12,%rdi
  38ef1e:	call   737b0 <swift_bridgeObjectRelease@plt>
  38ef23:	mov    %r15,%rdi
  38ef26:	call   737b0 <swift_bridgeObjectRelease@plt>
  38ef2b:	jmp    38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38ef2d:	jb     38eed9 <$s8FrontEnd9TypeStoreV9unifiable33_27ADCF0684898ACFAE6641EE6EC9A869LL__9extending21handlingCoercionsWithSbAA5ArrowV_AiA17SubstitutionTableVzSbAA03AnyC8IdentityV_AMtXEtF03$s8a104End5TyperV5match33_A3D88A7B549457189E34B3066F923C6ALL_2inAC16ResolutionThreadAELLV8AdvancedOAH_AA13Scopes9VtFSbAA07rC12R0V_ANtXEfU_SayAM_AMtGTf1nnncn_n+0x319>
  38ef2f:	ud2
  38ef31:	ud2
  38ef33:	ud2
  38ef35:	data16 cs nopw 0x0(%rax,%rax,1)

